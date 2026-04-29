from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload   # ✅ added
from database import SessionLocal
from models.cart import CartItem
from models.product import Product
from schemas.cart import CartCreate
from utils.auth import get_current_user
import time

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ 1. ADD TO CART
@router.post("/cart")
def add_to_cart(
    data: CartCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if data.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "Invalid quantity"}
        )

    start_time = time.time()
    product = db.query(Product).filter(Product.id == data.product_id).first()
    print(f"⏱️ Product lookup took {time.time() - start_time:.4f} sec")

    if not product:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "message": "Product not found"}
        )

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

    return {
        "success": True,
        "message": "Added to cart"
    }


# ✅ 2. GET CART (N+1 FIXED + PRODUCT DETAILS)
@router.get("/cart")
def get_my_cart(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = "created_at",
    order: str = "desc",
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    offset = (page - 1) * limit

    # ✅ N+1 FIX → preload product
    query = db.query(CartItem).options(
        selectinload(CartItem.product)   # 🔥 KEY LINE
    ).filter(
        CartItem.user_id == current_user.id
    )

    # SORTING
    allowed_sort_fields = {
        "created_at": CartItem.created_at,
        "quantity": CartItem.quantity
    }

    if sort_by in allowed_sort_fields:
        column = allowed_sort_fields[sort_by]
        query = query.order_by(column.desc() if order == "desc" else column.asc())

    # ⏱️ COUNT
    start_time = time.time()
    total = query.count()
    print(f"⏱️ Cart count took {time.time() - start_time:.4f} sec")

    # ⏱️ FETCH
    start_time = time.time()
    cart_items = query.offset(offset).limit(limit).all()
    print(f"⏱️ Cart fetch took {time.time() - start_time:.4f} sec")

    # ✅ RESPONSE WITH PRODUCT DETAILS
    result = []
    for item in cart_items:
        result.append({
            "cart_id": item.id,
            "quantity": item.quantity,
            "product": {
                "id": item.product.id,
                "name": item.product.name,
                "price": item.product.price
            }
        })

    return {
        "success": True,
        "message": "Cart fetched successfully",
        "data": result,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total
        }
    }


# ✅ 3. DELETE CART ITEM
@router.delete("/cart/{id}")
def delete_cart(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    start_time = time.time()

    item = db.query(CartItem).filter(
        CartItem.id == id,
        CartItem.user_id == current_user.id
    ).first()

    print(f"⏱️ Delete lookup took {time.time() - start_time:.4f} sec")

    if not item:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "message": "Cart item not found"}
        )

    db.delete(item)
    db.commit()

    return {
        "success": True,
        "message": "Cart item deleted successfully"
    }