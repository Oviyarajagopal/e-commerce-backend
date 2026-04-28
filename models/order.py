from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from database import Base
import datetime


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,index=True)
    total_amount = Column(Float)
    status = Column(String(50), default="placed")  # placed, shipped, delivered
    created_at = Column(DateTime, default=datetime.datetime.utcnow,index=True)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer)
    quantity = Column(Integer)
    price = Column(Float)