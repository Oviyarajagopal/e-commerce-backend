from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException

# Import DB (NO create_all here)
from database import engine

# Import models (VERY IMPORTANT for Alembic + relationships)
from models import user, product, cart, order

# Import routers
from routers import product as product_router
from routers import cart as cart_router
from routers import order as order_router
from routers import auth
from routers import address
# (Add address router later when created)

app = FastAPI()

# ✅ Include routers
app.include_router(product_router.router)
app.include_router(cart_router.router)
app.include_router(order_router.router)
app.include_router(auth.router)
app.include_router(address.router)

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