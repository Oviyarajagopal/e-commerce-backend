from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.cart import CartItem
from models.product import Product
from schemas.cart import CartCreate
from utils.auth import get_current_user

router = APIRouter()


# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ Helper: serialize cart items
def serialize_cart(items):
    result = []
    for item in items:
        result.append({
            "cart_id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity
        })
    return result


# ✅ 1. ADD TO CART
@router.post("/cart")
def add_to_cart(
    data: CartCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity")

    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # ✅ Check existing item
    existing_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == data.product_id
    ).first()

    if existing_item:
        existing_item.quantity += data.quantity
    else:
        item = CartItem(
            user_id=current_user.id,
            product_id=data.product_id,
            quantity=data.quantity
        )
        db.add(item)

    db.commit()

    return {"message": "Added to cart"}


# ✅ 2. GET CART (CLEAN RESPONSE)
@router.get("/cart")
def get_my_cart(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).all()

    return serialize_cart(cart_items)


# ✅ 3. DELETE CART ITEM
@router.delete("/cart/{id}")
def delete_cart(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    item = db.query(CartItem).filter(
        CartItem.id == id,
        CartItem.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    db.delete(item)
    db.commit()

    return {"message": "Deleted"}