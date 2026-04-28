from pydantic import BaseModel, EmailStr


# ✅ INPUT SCHEMA (register)
class UserCreate(BaseModel):
    email: EmailStr   # ✅ validates email format
    password: str


# ✅ RESPONSE SCHEMA (safe output)
class UserResponse(BaseModel):
    id: int
    email: EmailStr

class Config:
    from_attributes = True 

# ✅ LOGIN RESPONSE (token structure)
class TokenResponse(BaseModel):
    access_token: str
    token_type: str