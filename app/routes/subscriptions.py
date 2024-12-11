from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_subscriptions():
    return {"message": "Subscriptions endpoint"}
