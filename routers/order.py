from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import SessionLocal
from models.cart import CartItem
from models.product import Product
from models.order import Order, OrderItem
from utils.auth import get_current_user
import time

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ Background Email Function
def send_order_email(email: str, order_id: int, total: float):
    print(f"""
📧 Sending Email...
To: {email}

Hello,
Your order #{order_id} has been placed successfully!
Total Amount: ₹{total}

Thank you for shopping!
""")


# ✅ PLACE ORDER (FIXED N+1)
@router.post("/orders/place")
def place_order(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    api_start = time.time()

    # 1️⃣ Fetch cart
    start = time.time()
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).all()
    end = time.time()
    print(f"⏱️ Fetch cart took {end - start:.4f} sec")

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "Cart is empty"}
        )

    # ✅ 🔥 FIX: Fetch all products in ONE query
    start = time.time()

    product_ids = [item.product_id for item in cart_items]

    products = db.query(Product).filter(Product.id.in_(product_ids)).all()

    product_map = {p.id: p for p in products}

    end = time.time()
    print(f"⏱️ Bulk product fetch took {end - start:.4f} sec")

    total_amount = 0

    # 2️⃣ Validate + calculate total (NO DB CALL HERE)
    start = time.time()

    for item in cart_items:
        product = product_map.get(item.product_id)

        if not product:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "message": "Product not found"}
            )

        if product.stock < item.quantity:
            raise HTTPException(
                status_code=409,
                detail={"success": False, "message": "Out of stock"}
            )

        total_amount += product.price * item.quantity

    end = time.time()
    print(f"⏱️ Validation took {end - start:.4f} sec")

    # 3️⃣ Create order
    start = time.time()

    order = Order(
        user_id=current_user.id,
        total_amount=total_amount
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    end = time.time()
    print(f"⏱️ Create order took {end - start:.4f} sec")

    # 4️⃣ Create order items + update stock (NO DB CALL)
    start = time.time()

    for item in cart_items:
        product = product_map[item.product_id]

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            price=product.price
        )

        product.stock -= item.quantity
        db.add(order_item)

    end = time.time()
    print(f"⏱️ Create order items took {end - start:.4f} sec")

    # 5️⃣ Clear cart
    start = time.time()

    db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).delete()

    db.commit()

    end = time.time()
    print(f"⏱️ Clear cart took {end - start:.4f} sec")

    # 6️⃣ Background email
    background_tasks.add_task(
        send_order_email,
        current_user.email,
        order.id,
        total_amount
    )

    api_end = time.time()
    print(f"🚀 Total API time: {api_end - api_start:.4f} sec")

    return {
        "success": True,
        "message": "Order placed successfully",
        "data": {
            "order_id": order.id,
            "total_amount": total_amount
        }
    }
