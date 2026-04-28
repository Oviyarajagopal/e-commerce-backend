from sqlalchemy import Column, Integer, ForeignKey
from database import Base

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"),index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)