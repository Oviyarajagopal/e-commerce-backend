from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from models.user import User, Address
import datetime

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    price = Column(Float, nullable=False,index=True)
    stock = Column(Integer, default=0)
    category = Column(String(100),index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow,index=True)