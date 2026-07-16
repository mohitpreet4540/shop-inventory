from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from app.database import SessionLocal
from app import schemas, models

router = APIRouter(prefix="/api/orders", tags=["Orders & Billing"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =================================================================
# THE TRANSACTIONAL CHECKOUT ENGINE
# =================================================================
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(order_data: schemas.OrderCreate, db: Session = Depends(get_db)):
    try:
        # 🌟 FIX 1: Consolidate cart quantities by product_id to prevent validation bypass
        consolidated_quantities = {}
        for item in order_data.items:
            consolidated_quantities[item.product_id] = consolidated_quantities.get(item.product_id, Decimal("0.00")) + item.quantity

        # 🌟 FIX 2: Lock rows using with_for_update() to prevent concurrent checkout race conditions
        for product_id, total_qty in consolidated_quantities.items():
            product = db.query(models.Product).filter(models.Product.id == product_id).with_for_update().first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
            if product.current_quantity < total_qty:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient stock for {product.name}. Requested total: {total_qty}, Available: {product.current_quantity}"
                )

        # Initialize base order row configuration
        new_order = models.Order(
            total_amount=Decimal("0.00"),  # Calculated dynamically below
            amount_paid=order_data.amount_paid,
            amount_pending=Decimal("0.00"),
            payment_method=order_data.payment_method,
            payment_status=order_data.payment_status,
            customer_id=order_data.customer_id,
            customer_info=order_data.customer_info
        )
        db.add(new_order)
        db.flush()  # Populates new_order.id ahead of execution updates

        total_amount = Decimal("0.00")
        for item in order_data.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            sell_price = product.selling_price
            cost_price = product.cost_price
            quantity = item.quantity
            
            item_total = sell_price * quantity
            total_amount += item_total
            
            # Save invoice line item detail
            db.add(models.OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=sell_price
            ))
            
            # Deduct physical inventory holdings safely
            product.current_quantity -= quantity
            
            # Record structural transaction history trail
            db.add(models.StockTransaction(
                product_id=product.id,
                type="SALE",
                quantity_changed=-quantity,
                unit_cost=cost_price,
                total_cost=quantity * cost_price,
                notes=f"Automated POS Checkout deduction. Order Ref #{new_order.id}"
            ))

        # Complete final bill accounting balances
        new_order.total_amount = total_amount
        pending_debt = total_amount - order_data.amount_paid
        new_order.amount_pending = max(Decimal("0.00"), pending_debt)

        # 🌟 FIX 3: Accrue unpaid balances directly to the Customer's Khata Profile
        if pending_debt > 0:
            if not order_data.customer_id:
                raise HTTPException(
                    status_code=400,
                    detail="A valid customer profile registration ID is mandatory for Credit/Partial transactions."
                )
            customer = db.query(models.Customer).filter(models.Customer.id == order_data.customer_id).first()
            if not customer:
                raise HTTPException(status_code=404, detail="Selected Customer account profile not found.")
            customer.total_credit_due += pending_debt

        # Document physical cash drawer receipts into Finance Ledger
        if order_data.amount_paid > 0:
            db.add(models.FinanceLedger(
                type="INCOME",
                amount=order_data.amount_paid,
                category="SALES",
                notes=f"Cash/Digital payment generated from Order Reference #{new_order.id}"
            ))

        db.commit()
        return {"message": "Order processed successfully", "order_id": new_order.id, "total_bill": total_amount}

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Database Transaction Crash: {str(e)}")