from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import SessionLocal
from models.cart import CartItem
from models.product import Product
from models.order import Order, OrderItem
from utils.auth import get_current_user

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


# ✅ PLACE ORDER (WITH BACKGROUND TASK)
@router.post("/orders/place")
def place_order(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 1️⃣ Get user cart
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total_amount = 0

    # 2️⃣ Validate stock + calculate total
    for item in cart_items:
        product = db.query(Product).filter(
            Product.id == item.product_id
        ).first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if product.stock < item.quantity:
            raise HTTPException(status_code=409, detail="Out of stock")

        total_amount += product.price * item.quantity

    # 3️⃣ Create order
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    # 4️⃣ Create order items + reduce stock
    for item in cart_items:
        product = db.query(Product).filter(
            Product.id == item.product_id
        ).first()

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            price=product.price
        )

        product.stock -= item.quantity
        db.add(order_item)

    # 5️⃣ Clear cart
    db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).delete()

    db.commit()

    # 🔥 6️⃣ BACKGROUND EMAIL (IMPORTANT)
    background_tasks.add_task(
        send_order_email,
        current_user.email,   # user email
        order.id,
        total_amount
    )

    return {"message": "Order placed successfully"}