from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import SessionLocal
from models.product import Product
from schemas.product import ProductCreate, ProductResponse
from config.redis_config import redis_client
import json
import time   

router = APIRouter()

RATE_LIMIT = 10
WINDOW = 60  # seconds

# ✅ FIXED RATE LIMIT (IMPORTANT)
def check_rate_limit(request: Request):
    if not redis_client:
        return

    ip = request.client.host
    key = f"rate_limit:{ip}"

    try:
        current = redis_client.get(key)

        if current:
            current = int(current)
            if current >= RATE_LIMIT:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "success": False,
                        "message": "Too many requests. Try again later."
                    }
                )
            redis_client.incr(key)
        else:
            redis_client.setex(key, WINDOW, 1)

    except HTTPException:
        raise 

    except Exception as e:
        print("Rate Limit Error:", e)

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ 1. CREATE PRODUCT
@router.post("/products")
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**data.dict())

    db.add(product)
    db.commit()
    db.refresh(product)

    try:
        if redis_client:
            redis_client.delete("products:list")
    except Exception as e:
        print("Redis Delete Error:", e)

    return {
        "success": True,
        "message": "Product created successfully",
        "data": ProductResponse.from_orm(product)
    }


# ✅ 2. GET ALL PRODUCTS
@router.get("/products")
def get_products(
    request: Request,  
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    search: str = None,
    sort_by: str = None,
    order: str = "asc",
    db: Session = Depends(get_db)
):
     # 🔥 RATE LIMIT CHECK
    check_rate_limit(request)

    offset = (page - 1) * limit

    cache_key = f"products:list:{page}:{limit}:{category}:{min_price}:{max_price}:{search}:{sort_by}:{order}"

    # ✅ CACHE READ
    try:
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                print("⚡ CACHE HIT")
                return json.loads(cached)
    except Exception as e:
        print("Redis Error:", e)

    print("🐢 CACHE MISS")

    query = db.query(Product)

    # ✅ FILTER
    if category:
        query = query.filter(Product.category == category)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # ✅ SEARCH
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )

    # ✅ SORT
    allowed_sort_fields = {
        "price": Product.price,
        "created_at": Product.created_at,
        "name": Product.name
    }

    if sort_by in allowed_sort_fields:
        column = allowed_sort_fields[sort_by]
        query = query.order_by(column.desc() if order == "desc" else column.asc())

    # ⏱️ COUNT TIMING
    start_time = time.time()
    total = query.count()
    end_time = time.time()
    print(f"⏱️ Count query took {end_time - start_time:.4f} sec")

    # ⏱️ FETCH TIMING
    start_time = time.time()
    products = query.offset(offset).limit(limit).all()
    end_time = time.time()
    print(f"⏱️ Fetch query took {end_time - start_time:.4f} sec")

    result = [ProductResponse.from_orm(p) for p in products]

    response = {
        "success": True,
        "message": "Products fetched successfully",
        "data": result,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total
        }
    }

    # ✅ CACHE WRITE
    try:
        if redis_client:
            redis_client.setex(cache_key, 60, json.dumps(response, default=str))
    except Exception as e:
        print("Redis Save Error:", e)

    return response


# ✅ 3. GET SINGLE PRODUCT
@router.get("/products/{id}")
def get_product(id: int, db: Session = Depends(get_db)):
    cache_key = f"product:{id}"

    try:
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                print("⚡ CACHE HIT")
                return json.loads(cached)
    except Exception as e:
        print("Redis Error:", e)

    start_time = time.time()

    product = db.query(Product).filter(Product.id == id).first()

    end_time = time.time()
    print(f"⏱️ Single product query took {end_time - start_time:.4f} sec")

    if not product:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "message": "Product not found"}
        )

    response = {
        "success": True,
        "message": "Product fetched successfully",
        "data": ProductResponse.from_orm(product)
    }

    try:
        if redis_client:
            redis_client.setex(cache_key, 60, json.dumps(response, default=str))
    except Exception as e:
        print("Redis Save Error:", e)

    return response


# ✅ 4. UPDATE PRODUCT
@router.put("/products/{id}")
def update_product(id: int, data: ProductCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "message": "Product not found"}
        )

    product.name = data.name
    product.description = data.description
    product.price = data.price
    product.stock = data.stock
    product.category = data.category

    db.commit()
    db.refresh(product)
    # 🔥 CLEAR CACHE
    try:
        if redis_client:
            redis_client.delete(f"product:{id}")
            redis_client.delete("products:list")
    except Exception as e:
        print("Redis Delete Error:", e)
    return {
        "success": True,
        "message": "Product updated successfully",
        "data": ProductResponse.from_orm(product)
    }


# ✅ 5. DELETE PRODUCT
@router.delete("/products/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "message": "Product not found"}
        )

    db.delete(product)
    db.commit()
    # 🔥 CLEAR CACHE
    try:
        if redis_client:
            redis_client.delete(f"product:{id}")
            redis_client.delete("products:list")
    except Exception as e:
        print("Redis Delete Error:", e)
        
    return {
        "success": True,
        "message": "Product deleted successfully"
    }