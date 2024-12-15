from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# Database Setup
DATABASE_URL = "sqlite:///./cloud_service.db"  # Update for production DB
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    api_permissions = Column(String, nullable=False)  # Comma-separated API names
    usage_limit = Column(Integer, nullable=False)

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))
    usage_count = Column(Integer, default=0)
    plan = relationship("SubscriptionPlan")

Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class PlanCreate(BaseModel):
    name: str
    description: Optional[str]
    api_permissions: List[str]
    usage_limit: int

class PlanUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    api_permissions: Optional[List[str]]
    usage_limit: Optional[int]

class SubscriptionAssign(BaseModel):
    user_id: str
    plan_id: int

# Dependency
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Admin Endpoints
@app.post("/plans")
async def create_plan(plan: PlanCreate, db: SessionLocal = Depends(get_db)):
    new_plan = SubscriptionPlan(
        name=plan.name,
        description=plan.description,
        api_permissions=",".join(plan.api_permissions),
        usage_limit=plan.usage_limit,
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return {"message": "Plan created", "plan_id": new_plan.id}

@app.put("/plans/{plan_id}")
async def update_plan(plan_id: int, plan: PlanUpdate, db: SessionLocal = Depends(get_db)):
    plan_data = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan_data:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan.name:
        plan_data.name = plan.name
    if plan.description:
        plan_data.description = plan.description
    if plan.api_permissions:
        plan_data.api_permissions = ",".join(plan.api_permissions)
    if plan.usage_limit:
        plan_data.usage_limit = plan.usage_limit

    db.commit()
    return {"message": "Plan updated"}

@app.delete("/plans/{plan_id}")
async def delete_plan(plan_id: int, db: SessionLocal = Depends(get_db)):
    plan_data = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan_data:
        raise HTTPException(status_code=404, detail="Plan not found")

    db.delete(plan_data)
    db.commit()
    return {"message": "Plan deleted"}

# User Subscription Endpoints
@app.put("/subscriptions")
async def assign_subscription(subscription: SubscriptionAssign, db: SessionLocal = Depends(get_db)):
    user_subscription = db.query(UserSubscription).filter(UserSubscription.user_id == subscription.user_id).first()

    if user_subscription:
        user_subscription.plan_id = subscription.plan_id
        user_subscription.usage_count = 0
    else:
        new_subscription = UserSubscription(user_id=subscription.user_id, plan_id=subscription.plan_id)
        db.add(new_subscription)

    db.commit()
    return {"message": "Subscription updated"}

@app.get("/subscriptions/{user_id}")
async def get_subscription(user_id: str, db: SessionLocal = Depends(get_db)):
    user_subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if not user_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    plan = user_subscription.plan
    return {
        "user_id": user_subscription.user_id,
        "plan": {
            "name": plan.name,
            "description": plan.description,
            "api_permissions": plan.api_permissions.split(","),
            "usage_limit": plan.usage_limit,
        },
        "usage_count": user_subscription.usage_count,
    }

# Access Control
@app.get("/access/{user_id}/{api_request}")
async def check_access(user_id: str, api_request: str, db: SessionLocal = Depends(get_db)):
    user_subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if not user_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    plan = user_subscription.plan
    if api_request not in plan.api_permissions.split(","):
        raise HTTPException(status_code=403, detail="Access denied: API not permitted")

    if user_subscription.usage_count >= plan.usage_limit:
        raise HTTPException(status_code=403, detail="Access denied: Usage limit exceeded")

    user_subscription.usage_count += 1
    db.commit()
    return {"message": "Access granted"}
