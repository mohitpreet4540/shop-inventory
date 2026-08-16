from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user
from app import schemas, models

router = APIRouter(prefix="/api/returns", tags=["Returns & Refunds"])


# =================================================================
# 1. PROCESS A RETURN (Any logged-in role — happens at the counter)
# =================================================================
@router.post("/", response_model=schemas.ReturnResponse, status_code=status.HTTP_201_CREATED)
def create_return(
    payload: schemas.ReturnCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        order = db.query(models.Order).filter(models.Order.id == payload.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"Order #{payload.order_id} not found.")

        if payload.refund_method == "CREDIT_ADJUSTMENT" and not order.customer_id:
            raise HTTPException(
                status_code=400,
                detail="CREDIT_ADJUSTMENT requires the original order to have a registered customer."
            )

        refund_amount = Decimal("0.00")
        return_item_rows = []  # (order_item, product, quantity, restockable)

        for item in payload.items:
            order_item = db.query(models.OrderItem).filter(
                models.OrderItem.id == item.order_item_id,
                models.OrderItem.order_id == payload.order_id
            ).first()
            if not order_item:
                raise HTTPException(
                    status_code=404,
                    detail=f"Order item #{item.order_item_id} does not belong to order #{payload.order_id}."
                )

            # Prevent returning more than was actually sold, across possibly multiple return requests
            already_returned = db.query(func.coalesce(func.sum(models.ReturnItem.quantity_returned), Decimal("0.00"))).filter(
                models.ReturnItem.order_item_id == order_item.id
            ).scalar()

            returnable_remaining = order_item.quantity - already_returned
            if item.quantity > returnable_remaining:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Cannot return {item.quantity} units of order item #{order_item.id}. "
                        f"Only {returnable_remaining} units remain returnable "
                        f"(sold: {order_item.quantity}, already returned: {already_returned})."
                    )
                )

            product = db.query(models.Product).filter(
                models.Product.id == order_item.product_id
            ).with_for_update().first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product for order item #{order_item.id} no longer exists.")

            refund_amount += item.quantity * order_item.unit_price
            return_item_rows.append((order_item, product, item.quantity, item.restockable))

        # 2. RESTOCK (or write off) each returned item
        for order_item, product, quantity, restockable in return_item_rows:
            if restockable:
                # We don't track which specific batch(es) fed the original sale, so returned
                # stock goes into its own clearly-labeled batch rather than guessing an expiry.
                db.add(models.StockBatch(
                    product_id=product.id,
                    quantity_received=quantity,
                    quantity_remaining=quantity,
                    unit_cost=product.cost_price,
                    expiry_date=None,
                    notes=f"Returned stock from Order #{order_item.order_id}. Verify condition/expiry before resale.",
                ))
                product.current_quantity += quantity

                db.add(models.StockTransaction(
                    product_id=product.id,
                    type="RETURN_RESTOCK",
                    quantity_changed=quantity,
                    unit_cost=product.cost_price,
                    total_cost=quantity * product.cost_price,
                    notes=f"Customer return from Order #{order_item.order_id}.",
                ))
            else:
                # Damaged/expired — logged for audit purposes but NOT added back to sellable stock.
                db.add(models.StockTransaction(
                    product_id=product.id,
                    type="RETURN_WRITEOFF",
                    quantity_changed=Decimal("0.00"),
                    unit_cost=product.cost_price,
                    total_cost=quantity * product.cost_price,
                    notes=f"Non-restockable return from Order #{order_item.order_id} (write-off).",
                ))

        # 3. PROCESS THE REFUND
        if payload.refund_method == "CREDIT_ADJUSTMENT":
            customer = db.query(models.Customer).filter(models.Customer.id == order.customer_id).with_for_update().first()
            if not customer:
                raise HTTPException(status_code=404, detail="Customer profile for this order was not found.")
            # Reduce what they owe, floored at zero — refund value can't push their balance negative here.
            customer.total_credit_due = max(Decimal("0.00"), customer.total_credit_due - refund_amount)
        else:
            # CASH or ONLINE — real money leaving the register
            db.add(models.FinanceLedger(
                type="EXPENSE",
                amount=refund_amount,
                category="REFUND",
                is_automated=True,
                notes=f"Refund ({payload.refund_method}) for Order #{payload.order_id}. Reason: {payload.reason}.",
            ))

        # 4. CREATE THE RETURN RECORD
        new_return = models.Return(
            order_id=payload.order_id,
            processed_by_user_id=current_user.id,
            reason=payload.reason,
            refund_method=payload.refund_method,
            refund_amount=refund_amount,
            notes=payload.notes,
        )
        db.add(new_return)
        db.flush()

        for order_item, product, quantity, restockable in return_item_rows:
            db.add(models.ReturnItem(
                return_id=new_return.id,
                order_item_id=order_item.id,
                product_id=product.id,
                quantity_returned=quantity,
                unit_price=order_item.unit_price,
                restockable=restockable,
            ))

        db.commit()
        db.refresh(new_return)
        return new_return

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process return: {str(e)}")


# =================================================================
# 2. LIST RETURNS FOR A SPECIFIC ORDER (Any logged-in role)
# =================================================================
@router.get("/order/{order_id}", response_model=List[schemas.ReturnResponse])
def list_returns_for_order(order_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Return).filter(models.Return.order_id == order_id).order_by(models.Return.timestamp.desc()).all()


# =================================================================
# 3. LIST ALL RETURNS (Any logged-in role)
# =================================================================
@router.get("/", response_model=List[schemas.ReturnResponse])
def list_all_returns(
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Return)
    if reason:
        query = query.filter(models.Return.reason == reason)
    return query.order_by(models.Return.timestamp.desc()).all()
