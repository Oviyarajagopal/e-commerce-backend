from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User
from schemas.user import UserCreate
from utils.auth import hash_password, verify_password, create_access_token

router = APIRouter()


# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ REGISTER
@router.post("/register")
def register(data: UserCreate, db: Session = Depends(get_db)):
    hashed_pw = hash_password(data.password)

    user = User(
        email=data.email,
        password=hashed_pw
    )

    db.add(user)
    db.commit()

    return {"message": "User created"}


# ✅ LOGIN
@router.post("/login")
def login(data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer"
    }