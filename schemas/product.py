from pydantic import BaseModel


# ✅ INPUT SCHEMA (used for creating/updating)
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category: str


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int
    category: str

    class Config:
        from_attributes = True   # ✅ THIS LINE FIXES YOUR ERROR