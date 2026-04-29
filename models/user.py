from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True,index=True)
    password = Column(String(255))
    
    phone_number = Column(String(15), nullable=True)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 🔗 Relationships
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")
    addresses = relationship("Address", back_populates="user")


   
class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    full_name = Column(String)
    phone = Column(String)
    address_line = Column(String)
    city = Column(String)
    state = Column(String)
    pincode = Column(String)
    country = Column(String)

    user = relationship("User", back_populates="addresses")
    order_items = relationship("OrderItem", back_populates="address")

    