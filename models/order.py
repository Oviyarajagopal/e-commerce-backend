from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from models.user import User, Address
from database import Base
import datetime

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    # ✅ FIXED: added ForeignKey
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    total_amount = Column(Float)
    status = Column(String(50), default="placed")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
  # ✅ NEW FIELD
    address_id = Column(Integer, ForeignKey("addresses.id"))


    # ✅ relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price = Column(Float)
    address_id = Column(Integer, ForeignKey("addresses.id"))  
    # ✅ ADD THESE
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
      # ✅ NEW RELATION
    address = relationship("Address", back_populates="orders")
    address = relationship("Address", back_populates="order_items")