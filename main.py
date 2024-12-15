from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# MySQL Database Configuration
DATABASE_URL = "mysql+pymysql://cloud_admin:SecurePass123!@localhost/cloud_service_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    api_permissions = Column(String, nullable=False)  # Comma-separated APIs
    usage_limit = Column(Integer, nullable=False)

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))
    usage_count = Column(Integer, default=0)
    plan = relationship("SubscriptionPlan")

# Create tables in the database
Base.metadata.create_all(bind=engine)

# FastAPI Application
app = FastAPI()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

# Admin: Create a Subscription Plan
@app.post("/plans")
async def create_plan(plan: PlanCreate, db: SessionLocal = Depends(get_db)):
    # Check if a plan with the same name already exists
    existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == plan.name).first()
    if existing_plan:
        raise HTTPException(status_code=400, detail="Plan with this name already exists")

    # If no duplicate, insert the plan
    new_plan = SubscriptionPlan(
        name=plan.name,
        description=plan.description,
        api_permissions=",".join(plan.api_permissions),
        usage_limit=plan.usage_limit,
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return {"message": "Plan created successfully", "plan_id": new_plan.id}

# Admin: Update a Subscription Plan
@app.put("/plans/{plan_id}")
async def update_plan(plan_id: int, plan: PlanUpdate, db: SessionLocal = Depends(get_db)):
    existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not existing_plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan.name:
        existing_plan.name = plan.name
    if plan.description:
        existing_plan.description = plan.description
    if plan.api_permissions:
        existing_plan.api_permissions = ",".join(plan.api_permissions)
    if plan.usage_limit:
        existing_plan.usage_limit = plan.usage_limit

    db.commit()
    return {"message": "Plan updated successfully"}

# Admin: Delete a Subscription Plan
@app.delete("/plans/{plan_id}")
async def delete_plan(plan_id: int, db: SessionLocal = Depends(get_db)):
    existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not existing_plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    db.delete(existing_plan)
    db.commit()
    return {"message": "Plan deleted successfully"}

# Admin: Assign/Update User Subscription
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
    return {"message": "Subscription assigned or updated successfully"}

# User: Get Subscription Details
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

# Access Control: Check if API Access is Allowed
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
