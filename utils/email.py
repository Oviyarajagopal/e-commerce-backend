def send_order_email(email: str, order_id: int, total: float):
    print("\n📧 Sending Email...")
    print(f"To: {email}")
    print(f"""
Hello,

Your order #{order_id} has been placed successfully.
Total: ₹{total}

Thank you for shopping with us!
""")