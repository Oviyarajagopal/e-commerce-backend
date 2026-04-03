from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas import UserCreate, UserLogin
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)

app = FastAPI()

security = HTTPBearer()

# Temporary storage
users = []


# 🔐 Get current user from token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    email = verify_token(token)

    if email is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return email


# 🏠 Root (optional but useful)
@app.get("/")
def root():
    return {"message": "API is running 🚀"}


# 🔒 Protected Route
@app.get("/profile")
def get_profile(current_user: str = Depends(get_current_user)):
    return {
        "message": "Access granted",
        "user": current_user
    }


# ✅ Register
@app.post("/register")
def register_user(user: UserCreate):
    user_data = user.dict()

    # Check if user already exists
    for db_user in users:
        if db_user["email"] == user_data["email"]:
            raise HTTPException(status_code=400, detail="User already exists")

    # 🔐 Hash password
    user_data["password"] = hash_password(user_data["password"])

    users.append(user_data)

    return {"message": "User registered successfully"}


# 🔑 Login
@app.post("/login")
def login_user(user: UserLogin):
    for db_user in users:
        if db_user["email"] == user.email:

            # Verify password
            if verify_password(user.password, db_user["password"]):

                token = create_access_token({"sub": user.email})

                return {
                    "access_token": token,
                    "token_type": "bearer"
                }

            raise HTTPException(status_code=400, detail="Invalid password")

    raise HTTPException(status_code=404, detail="User not found")