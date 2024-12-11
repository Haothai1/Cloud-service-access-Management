from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_plans():
    return {"message": "Plans endpoint"}
