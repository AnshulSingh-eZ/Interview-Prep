from fastapi import APIRouter, Depends
from app.models.user import User
from app.auth.dependencies import get_current_user
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "name": str(current_user.name),
        "email": str(current_user.email)
    }