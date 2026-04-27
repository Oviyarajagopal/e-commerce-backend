from pydantic import BaseModel


# ✅ INPUT SCHEMA (for adding to cart)
class CartCreate(BaseModel):
    product_id: int
    quantity: int


# ✅ RESPONSE SCHEMA (for API output)
class CartResponse(BaseModel):
    cart_id: int
    product_id: int
    quantity: int

    class Config:
        orm_mode = True