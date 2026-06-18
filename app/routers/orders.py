from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal  
from datetime import datetime, timezone  # 🌟 Swapped to standard timezone structures
from app.database import get_db
from app.models import Product, Order, OrderItem, StockTransaction
from app.schemas import OrderCreateSchema, OrderResponseSchema

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=OrderResponseSchema)
def checkout_cart(payload: OrderCreateSchema, db: Session = Depends(get_db)):
    running_total = Decimal("0.00") 
    
    order_items_to_create = []
    products_to_update = []
    stock_logs_to_create = []
    
    try:
        for item in payload.items:
            product = None
            
            if item.barcode:
                product = db.query(Product).filter(Product.barcode == item.barcode).first()
                if not product:
                    raise HTTPException(status_code=404, detail=f"Scanned barcode '{item.barcode}' not found in inventory!")
            elif item.product_id:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if not product:
                    raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found!")
            else:
                raise HTTPException(status_code=400, detail="Each cart item must contain either a product_id or a barcode.")
            
            if product.current_quantity < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Inadequate inventory for '{product.name}' ({product.brand}). Requested: {item.quantity} {product.unit_type}, Available: {product.current_quantity}"
                )
            
            item_total = product.selling_price * item.quantity
            running_total += item_total  
            
            product.current_quantity -= item.quantity
            products_to_update.append(product)
            
            order_items_to_create.append({
                "product": product,
                "quantity": item.quantity,
                "unit_price": product.selling_price
            })
            stock_logs_to_create.append((product.id, item.quantity))

        if abs(running_total - payload.total_amount) > Decimal("0.01"):
            raise HTTPException(
                status_code=400,
                detail=f"Financial Integrity Breach: Calculated total (₹{running_total}) does not match payload total (₹{payload.total_amount})."
            )

        if payload.amount_pending > 0:
            calculated_status = "PARTIAL" if payload.amount_paid > 0 else "UNPAID"
        else:
            calculated_status = "PAID"

        # 🌟 FIXED: Created standard timezone-aware UTC timestamp entry
        new_order = Order(
            total_amount=payload.total_amount,
            amount_paid=payload.amount_paid,
            amount_pending=payload.amount_pending,
            payment_method=payload.payment_method.upper(),
            payment_status=calculated_status,
            customer_info=payload.customer_info,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(new_order)
        db.flush() 

        receipt_items_breakdown = []
        for line in order_items_to_create:
            prod = line["product"]
            
            oi = OrderItem(
                order_id=new_order.id, 
                product_id=prod.id, 
                quantity=line["quantity"], 
                unit_price=line["unit_price"]
            )
            db.add(oi)
            
            receipt_items_breakdown.append({
                "product_id": prod.id,
                "product_name": prod.name,
                "brand": prod.brand,
                "unit_type": prod.unit_type,
                "quantity": line["quantity"],
                "unit_price": line["unit_price"]
            })

        for prod_id, qty in stock_logs_to_create:
            log = StockTransaction(
                product_id=prod_id,
                quantity_changed=-qty, 
                type="SALE",
                notes=f"Automated deduction from Order #{new_order.id}. Customer Account: {payload.customer_info}"
            )
            db.add(log)

        db.commit() 
        
        return {
            "id": new_order.id,
            "total_amount": new_order.total_amount,
            "amount_paid": new_order.amount_paid,
            "amount_pending": new_order.amount_pending,
            "payment_method": new_order.payment_method,
            "payment_status": new_order.payment_status,
            "customer_info": new_order.customer_info,
            "timestamp": new_order.timestamp,
            "items": receipt_items_breakdown 
        }

    except HTTPException as http_ex:
        db.rollback()
        raise http_ex
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Checkout execution failed: {str(e)}")