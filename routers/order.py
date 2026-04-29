from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import SessionLocal
from models.cart import CartItem
from models.product import Product
from models.order import Order, OrderItem
from models.user import Address
from schemas.order import OrderCreate
from utils.auth import get_current_user
from sqlalchemy.orm import selectinload
from utils.email import send_order_email
import time

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@router.post("/orders")
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # ✅ Check address belongs to user
    address = db.query(Address).filter(
        Address.id == order_data.address_id,
        Address.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(status_code=400, detail="Invalid address")

    # Get cart items
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total_amount = 0
    order = Order(
        user_id=current_user.id,
        address_id=order_data.address_id
    )

    db.add(order)
    db.flush()

    for item in cart_items:
        product = db.query(Product).get(item.product_id)

        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=product.price
        )

        total_amount += product.price * item.quantity
        db.add(order_item)

    order.total_amount = total_amount

    # clear cart
    db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).delete()

    db.commit()

    return {
        "message": "Order placed successfully",
        "order_id": order.id,
        "total_amount": total_amount
    }

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



# ✅ GET ALL ORDERS (EAGER LOADING)
@router.get("/orders")
def get_orders(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    start = time.time()

    orders = db.query(Order).options(
        selectinload(Order.user),  
        selectinload(Order.items).selectinload(OrderItem.product)
    ).filter(
        Order.user_id == current_user.id
    ).all()

    end = time.time()
    print(f"⏱️ Orders fetch with eager loading took {end - start:.4f} sec")

    result = []

    for order in orders:
        result.append({
            "order_id": order.id,
            "total_amount": order.total_amount,
            "user": {
                "id": order.user.id,
                "email": order.user.email
            },
            "items": [
                {
                    "product_id": item.product.id,
                    "product_name": item.product.name,
                    "price": item.price,
                    "quantity": item.quantity
                }
                for item in order.items
            ]
        })

    return {
        "success": True,
        "message": "Orders fetched successfully",
        "data": result
    }