from sqlalchemy import Column, Integer, ForeignKey, DateTime
from database import Base
from sqlalchemy.sql import func
from models.user import User, Address
from sqlalchemy.orm import relationship

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"),index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    
    product = relationship("Product")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="cart_items")
