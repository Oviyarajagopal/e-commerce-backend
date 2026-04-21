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

    try:
        if redis_client:
            redis_client.delete("products:list")
    except Exception as e:
        print("Redis Delete Error:", e)

    return product


# ✅ 2. GET ALL PRODUCTS
@router.get("/products")
def get_products(
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    cache_key = "products:list"

    if not any([category, min_price, max_price, search]):
        try:
            if redis_client:
                cached = redis_client.get(cache_key)
                if cached:
                    print("CACHE HIT ✅")
                    return json.loads(cached)
        except Exception as e:
            print("Redis Error:", e)

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

    if not any([category, min_price, max_price, search]):
        try:
            if redis_client:
                redis_client.setex(cache_key, 60, json.dumps(result))
        except Exception as e:
            print("Redis Save Error:", e)

    return result


# ✅ 3. ⭐ IMPORTANT: RECENT FIRST (FIX)
@router.get("/products/recent")
def get_recent_products(db: Session = Depends(get_db)):
    recent_key = "recent:user:1"

    try:
        if redis_client:
            ids = redis_client.lrange(recent_key, 0, 4)
            ids = [int(i) for i in ids]
        else:
            return []
    except Exception as e:
        print("Redis Error:", e)
        return []

    if not ids:
        return []

    products = db.query(Product).filter(Product.id.in_(ids)).all()
    return serialize(products)


# ✅ 4. GET SINGLE PRODUCT
@router.get("/products/{id}")
def get_product(id: int, db: Session = Depends(get_db)):
    cache_key = f"product:{id}"

    try:
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                print("CACHE HIT ✅")
                return json.loads(cached)
    except Exception as e:
        print("Redis Error:", e)

    print("CACHE MISS ❌")

    product = db.query(Product).filter(Product.id == id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = serialize([product])[0]

    try:
        if redis_client:
            redis_client.setex(cache_key, 60, json.dumps(result))
    except Exception as e:
        print("Redis Save Error:", e)

    # 🔥 Recently viewed
    try:
        if redis_client:
            recent_key = "recent:user:1"
            redis_client.lpush(recent_key, id)
            redis_client.ltrim(recent_key, 0, 4)
    except Exception as e:
        print("Redis Recent Error:", e)

    return result


# ✅ 5. UPDATE PRODUCT
@router.put("/products/{id}")
def update_product(id: int, data: ProductCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = data.name
    product.description = data.description
    product.price = data.price
    product.stock = data.stock
    product.category = data.category

    db.commit()
    db.refresh(product)

    try:
        if redis_client:
            redis_client.delete("products:list")
            redis_client.delete(f"product:{id}")
    except Exception as e:
        print("Redis Delete Error:", e)

    return product


# ✅ 6. DELETE PRODUCT
@router.delete("/products/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    try:
        if redis_client:
            redis_client.delete("products:list")
            redis_client.delete(f"product:{id}")
    except Exception as e:
        print("Redis Delete Error:", e)

    return {"message": "Product deleted successfully"}