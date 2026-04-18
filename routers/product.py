from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.product import Product
from schemas.product import ProductCreate

router = APIRouter()


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
    query = db.query(Product)

    # ✅ Filter by category
    if category:
        query = query.filter(Product.category == category)

    # ✅ Filter by minimum price
    if min_price:
        query = query.filter(Product.price >= min_price)

    # ✅ Filter by maximum price
    if max_price:
        query = query.filter(Product.price <= max_price)

    # ✅ Search by product name
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    products = query.all()
    return products


# ✅ 3. GET SINGLE PRODUCT
@router.get("/products/{id}")
def get_product(id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product