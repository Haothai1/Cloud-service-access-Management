from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_access():
    return {"message": "Access endpoint"}
