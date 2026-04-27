from pydantic import BaseModel


# ✅ INPUT SCHEMA (used for creating/updating)
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category: str


# ✅ RESPONSE SCHEMA (used for API output - reduced fields)
class ProductResponse(BaseModel):
    id: int
    name: str
    price: float

    class Config:
        orm_mode = True