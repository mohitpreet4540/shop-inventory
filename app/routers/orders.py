from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal  #  Imported Decimal to match the database types perfectly
import datetime
from app.database import get_db
from app.models import Product, Order, OrderItem, StockTransaction
from app.schemas import OrderCreateSchema, OrderResponseSchema

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=OrderResponseSchema)
def checkout_cart(payload: OrderCreateSchema, db: Session = Depends(get_db)):
    #  FIX: Initialized running_total as a Decimal instead of a float (0.0)
    running_total = Decimal("0.00") 
    
    order_items_to_create = []
    products_to_update = []
    stock_logs_to_create = []
    
    try:
        # STEP 1: Loop and validate stock levels first
        for item in payload.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")
            
            if product.current_quantity < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Inadequate inventory for '{product.name}'. Requested: {item.quantity}, Available: {product.current_quantity}"
                )
            
            # Precise Decimal calculation for item and grand total
            item_total = product.selling_price * Decimal(item.quantity)
            running_total += item_total  # 🌟 This will NOT crash anymore! Both are Decimal now.
            
            # Stage updates in memory
            product.current_quantity -= item.quantity
            products_to_update.append(product)
            
            order_items_to_create.append((product.id, item.quantity, item_total))
            stock_logs_to_create.append((product.id, item.quantity))

        # STEP 2: Create Parent Order Entry
        new_order = Order(
            total_amount=running_total,
            payment_method=payload.payment_method.upper(),
            payment_status="PAID" if payload.payment_method.upper() == "ONLINE" else "PENDING",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(new_order)
        db.flush() 

        # STEP 3: Save child rows and write stock decrement ledger logs
        for prod_id, qty, price in order_items_to_create:
            oi = OrderItem(order_id=new_order.id, product_id=prod_id, quantity=qty, unit_price=price)
            db.add(oi)

        for prod_id, qty in stock_logs_to_create:
            log = StockTransaction(
                product_id=prod_id,
                quantity_changed=-qty, # Negative number tracks stock outgoing
                type="SALE",
                notes=f"Automated deduction from Order #{new_order.id}"
            )
            db.add(log)

        db.commit() 
        db.refresh(new_order)
        return new_order

    except HTTPException as http_ex:
        db.rollback()
        raise http_ex
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Checkout execution failed: {str(e)}")