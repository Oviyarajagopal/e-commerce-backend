from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.product import Product
from schemas.product import ProductCreate
from config.redis_config import redis_client
import json

router = APIRouter()


# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ Helper: safe serialize (handles datetime)
def serialize(products):
    result = []
    for p in products:
        data = {}
        for column in p.__table__.columns:
            value = getattr(p, column.name)

            # ✅ Fix datetime issue
            if value is not None and "datetime" in str(type(value)):
                value = str(value)

            data[column.name] = value

        result.append(data)
    return result


# ✅ 1. CREATE PRODUCT
@router.post("/products")
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**data.dict())

    db.add(product)
    db.commit()
    db.refresh(product)

    # 🔥 Cache Invalidation
    if redis_client:
        redis_client.delete("products:list")

    return product


# ✅ 2. GET ALL PRODUCTS (WITH CACHE)
@router.get("/products")
def get_products(
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    cache_key = "products:list"

    try:
        # ✅ Only cache when no filters
        if not any([category, min_price, max_price, search]):
            if redis_client:
                cached = redis_client.get(cache_key)
                if cached:
                    print("CACHE HIT ✅")
                    return json.loads(cached)

        print("CACHE MISS ❌")

        query = db.query(Product)

        if category:
            query = query.filter(Product.category == category)

        if min_price:
            query = query.filter(Product.price >= min_price)

        if max_price:
            query = query.filter(Product.price <= max_price)

        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))

        products = query.all()
        result = serialize(products)

        # ✅ Save cache only if no filters
        if not any([category, min_price, max_price, search]):
            if redis_client:
                redis_client.setex(cache_key, 60, json.dumps(result))

        return result

    except Exception as e:
        print("Error:", e)
        return []


# ✅ 3. GET SINGLE PRODUCT (WITH CACHE)
@router.get("/products/{id}")
def get_product(id: int, db: Session = Depends(get_db)):
    cache_key = f"product:{id}"

    try:
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                print("CACHE HIT ✅")
                return json.loads(cached)

        print("CACHE MISS ❌")

    except Exception as e:
        print("Redis Error:", e)

    product = db.query(Product).filter(Product.id == id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = serialize([product])[0]

    try:
        if redis_client:
            redis_client.setex(cache_key, 60, json.dumps(result))
    except Exception as e:
        print("Redis Save Error:", e)

    return result


# ✅ 4. UPDATE PRODUCT (WITH CACHE INVALIDATION)
@router.put("/products/{id}")
def update_product(id: int, data: ProductCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = data.name
    product.price = data.price
    product.category = data.category

    db.commit()
    db.refresh(product)

    # 🔥 Cache Invalidation
    if redis_client:
        redis_client.delete("products:list")
        redis_client.delete(f"product:{id}")

    return product


# ✅ 5. DELETE PRODUCT (WITH CACHE INVALIDATION)
@router.delete("/products/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    # 🔥 Cache Invalidation
    if redis_client:
        redis_client.delete("products:list")
        redis_client.delete(f"product:{id}")

    return {"message": "Product deleted successfully"}