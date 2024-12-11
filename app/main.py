from fastapi import FastAPI
from app.routes.permissions import router as permissions_router
from app.routes.plans import router as plans_router
from app.routes.subscriptions import router as subscriptions_router
from app.routes.access import router as access_router
from app.database import initialize_database

app = FastAPI()

app.include_router(permissions_router, prefix="/permissions", tags=["Permissions"])
app.include_router(plans_router, prefix="/plans", tags=["Plans"])
app.include_router(subscriptions_router, prefix="/subscriptions", tags=["Subscriptions"])
app.include_router(access_router, prefix="/access", tags=["Access Control"])
initialize_database()

