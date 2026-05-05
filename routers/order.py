from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, selectinload
from database import SessionLocal
from models.cart import CartItem
from models.product import Product
from models.order import Order, OrderItem
from models.user import Address  
from schemas.order import OrderCreate
from utils.auth import get_current_user
from utils.email import send_order_email
import time

router = APIRouter()


# 🔌 DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ CREATE ORDER FROM CART (WITH ADDRESS)
@router.post("/orders")
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        # ✅ Validate address ownership
        address = db.query(Address).filter(
            Address.id == order_data.address_id,
            Address.user_id == current_user.id
        ).first()

        if not address:
            raise HTTPException(status_code=400, detail="Invalid address")

        # ✅ Fetch cart
        cart_items = db.query(CartItem).filter(
            CartItem.user_id == current_user.id
        ).all()

        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        total_amount = 0

        # ✅ Create order
        order = Order(
            user_id=current_user.id,
            address_id=order_data.address_id
        )
        db.add(order)
        db.flush()

        # ✅ Process items
        for item in cart_items:
            product = db.query(Product).filter(
                Product.id == item.product_id
            ).first()

            if not product:
                raise HTTPException(status_code=404, detail="Product not found")

            if product.stock < item.quantity:
                raise HTTPException(status_code=409, detail="Out of stock")

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                price=product.price
            )

            total_amount += product.price * item.quantity
            product.stock -= item.quantity

            db.add(order_item)

        order.total_amount = total_amount

        # ✅ Clear cart
        db.query(CartItem).filter(
            CartItem.user_id == current_user.id
        ).delete()

        db.commit()

        return {
            "message": "Order placed successfully",
            "order_id": order.id,
            "total_amount": total_amount
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ✅ PLACE ORDER (OPTIMIZED + ADDRESS FIX)
@router.post("/orders/place")
def place_order(
    address_id: int,   # ✅ FIX: pass address from frontend
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    api_start = time.time()

    try:
        # ✅ Validate address
        address = db.query(Address).filter(
            Address.id == address_id,
            Address.user_id == current_user.id
        ).first()

        if not address:
            raise HTTPException(status_code=400, detail="Invalid address")

        # ✅ Fetch cart
        cart_items = db.query(CartItem).filter(
            CartItem.user_id == current_user.id
        ).all()

        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # ✅ Bulk fetch products
        product_ids = [item.product_id for item in cart_items]
        products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        product_map = {p.id: p for p in products}

        total_amount = 0

        # ✅ Validate + calculate
        for item in cart_items:
            product = product_map.get(item.product_id)

            if not product:
                raise HTTPException(status_code=404, detail="Product not found")

            if product.stock < item.quantity:
                raise HTTPException(status_code=409, detail="Out of stock")

            total_amount += product.price * item.quantity

        # ✅ Create order
        order = Order(
            user_id=current_user.id,
            address_id=address.id,
            total_amount=total_amount
        )
        db.add(order)
        db.flush()

        # ✅ Create order items + update stock
        for item in cart_items:
            product = product_map[item.product_id]

            db.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                price=product.price
            ))

            product.stock -= item.quantity

        # ✅ Clear cart
        db.query(CartItem).filter(
            CartItem.user_id == current_user.id
        ).delete()

        db.commit()

        # ✅ Background email
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

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ✅ GET ALL ORDERS (WITH ADDRESS ADDED)
@router.get("/orders")
def get_orders(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    orders = db.query(Order).options(
        selectinload(Order.user),
        selectinload(Order.address),   # ✅ NEW
        selectinload(Order.items).selectinload(OrderItem.product)
    ).filter(
        Order.user_id == current_user.id
    ).all()

    result = []

    for order in orders:
        result.append({
            "order_id": order.id,
            "total_amount": order.total_amount,
            "status": order.status,
            "address": {   # ✅ INCLUDE ADDRESS
                "full_name": order.address.full_name,
                "city": order.address.city,
                "pincode": order.address.pincode
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