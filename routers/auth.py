from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User
from schemas.user import UserCreate, UserResponse, TokenResponse
from utils.auth import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
import time   # ✅ added

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

    # ⏱️ CHECK EXISTING USER
    start = time.time()
    existing_user = db.query(User).filter(User.email == data.email).first()
    end = time.time()
    print(f"⏱️ Email check took {end - start:.4f} sec")

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Email already registered"
            }
        )

    # ⏱️ HASH PASSWORD
    start = time.time()
    hashed_pw = hash_password(data.password)
    end = time.time()
    print(f"⏱️ Password hashing took {end - start:.4f} sec")

    # ⏱️ CREATE USER
    start = time.time()

    user = User(
        email=data.email,
        password=hashed_pw
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    end = time.time()
    print(f"⏱️ User creation took {end - start:.4f} sec")

    return {
        "success": True,
        "message": "User registered successfully",
        "data": UserResponse.from_orm(user)
    }


# ✅ LOGIN
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # ⏱️ FETCH USER
    start = time.time()
    user = db.query(User).filter(User.email == form_data.username).first()
    end = time.time()
    print(f"⏱️ User fetch took {end - start:.4f} sec")

    if not user:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "message": "Invalid credentials"
            }
        )

    # ⏱️ PASSWORD VERIFY
    start = time.time()
    is_valid = verify_password(form_data.password, user.password)
    end = time.time()
    print(f"⏱️ Password verify took {end - start:.4f} sec")

    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "message": "Invalid credentials"
            }
        )

    # ⏱️ TOKEN CREATION
    start = time.time()
    token = create_access_token({"user_id": user.id})
    end = time.time()
    print(f"⏱️ Token creation took {end - start:.4f} sec")

    return {
        "success": True,
        "message": "Login successful",
        "data": TokenResponse(
            access_token=token,
            token_type="bearer"
        )
    }