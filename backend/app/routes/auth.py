from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, TokenResponse
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token

router = APIRouter(
    prefix = "/auth",
    tags=["Authentication"]
)
@router.post("/register")
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = (
        db.query(User).filter(User.email == user_data.email).first()
    )
    if existing_user:
        raise HTTPException(status_code = 400, detail="User Already Exists")    
    print(user_data.password, user_data.name, user_data.email, "______________________________")
    new_user = User(
        name = user_data.name, email = user_data.email, hashed_password = hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "message" : "Registration Successful!!",
        "user_id" : str(new_user.id)
    }
    
@router.post("/login", response_model=TokenResponse)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="New User? Register now!!"
        )
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid Credentials"
        )
    token = create_access_token(
        {"sub": str(user.id)}
    )
    return {
        "access_token": token,
        "token_type": "bearer"
    }   