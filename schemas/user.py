from pydantic import BaseModel, EmailStr, ConfigDict


# ✅ INPUT SCHEMA (register)
class UserCreate(BaseModel):
    email: EmailStr   # ✅ validates email format
    password: str


# ✅ RESPONSE SCHEMA (safe output)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)
class Config:
    from_attributes = True 

# ✅ LOGIN RESPONSE (token structure)
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    
    