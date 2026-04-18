from fastapi import FastAPI
from database import Base, engine

# Import models (VERY IMPORTANT)
from models import user, product, cart, order

# Import routers
from routers import product as product_router
from routers import cart as cart_router
from routers import order as order_router
from routers import auth

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(product_router.router)
app.include_router(cart_router.router)
app.include_router(order_router.router)
app.include_router(auth.router) 