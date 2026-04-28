from fastapi import FastAPI,Request
from database import Base, engine
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException

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

# ✅ Global HTTP Exception Handler
@app.exception_handler(FastAPIHTTPException)
async def custom_http_exception_handler(request: Request, exc: FastAPIHTTPException):
    message = exc.detail

    # If detail is dict (your custom)
    if isinstance(message, dict):
        message = message.get("message", "Error occurred")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": message
        }
    )


# ✅ Catch unexpected errors (500)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("Unhandled Error:", str(exc))

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error"
        }
    )