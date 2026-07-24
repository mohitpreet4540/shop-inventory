from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List
from app.database import get_db
from app.dependencies import get_current_user
from app import schemas, models

router = APIRouter(prefix="/api/orders", tags=["Orders & Billing"])


# =================================================================
# 🌟 NEW: FEFO (First-Expiry-First-Out) BATCH CONSUMPTION
# =================================================================
def _consume_batches_fefo(db: Session, product_id: int, quantity_needed: Decimal):
    """
    Deducts `quantity_needed` from a product's stock batches, oldest-expiring first.
    Non-expiring batches (expiry_date IS NULL) are consumed last.
    Returns the weighted-average unit cost across whatever batches were drawn from,
    for accurate per-sale profit tracking instead of relying on one blended cost figure.
    """
    batches = db.query(models.StockBatch).filter(
        models.StockBatch.product_id == product_id,
        models.StockBatch.quantity_remaining > 0
    ).order_by(
        models.StockBatch.expiry_date.is_(None),
        models.StockBatch.expiry_date.asc()
    ).with_for_update().all()

    remaining_to_consume = quantity_needed
    total_cost = Decimal("0.00")

    for batch in batches:
        if remaining_to_consume <= 0:
            break
        take = min(batch.quantity_remaining, remaining_to_consume)
        batch.quantity_remaining -= take
        total_cost += take * batch.unit_cost
        remaining_to_consume -= take

    if remaining_to_consume > 0:
        # Batch records are out of sync with product.current_quantity — a real data
        # integrity issue (e.g. stock adjusted outside the batch system).
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Stock batch records are out of sync for product ID {product_id} "
                f"(short by {remaining_to_consume} units). Reconcile via a new restock entry."
            )
        )

    return total_cost / quantity_needed if quantity_needed > 0 else Decimal("0.00")


# Any logged-in role (OWNER, ADMIN, CASHIER) can process checkout — this is the cashier's main job.
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(order_data: schemas.OrderCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        # 1. CONSOLIDATE CART QUANTITIES
        consolidated_quantities = {}
        for item in order_data.items:
            consolidated_quantities[item.product_id] = (
                consolidated_quantities.get(item.product_id, Decimal("0.00")) + item.quantity
            )

        # 2. CONCURRENCY CONTROL & STOCK VALIDATION
        for product_id, total_qty in consolidated_quantities.items():
            product = db.query(models.Product).filter(
                models.Product.id == product_id
            ).with_for_update().first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {product_id} not found."
                )

            if product.current_quantity < total_qty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for '{product.name}'. Requested: {total_qty}, Available: {product.current_quantity}"
                )

        # 3. INITIALIZE THE MASTER ORDER RECORD
        new_order = models.Order(
            total_amount=Decimal("0.00"),  # Calculated dynamically below
            amount_paid=order_data.amount_paid,
            amount_pending=Decimal("0.00"),  # Calculated dynamically below
            payment_method=order_data.payment_method,
            payment_status=order_data.payment_status,
            customer_id=order_data.customer_id,
            customer_info=order_data.customer_info
        )
        db.add(new_order)
        db.flush()

        total_order_amount = Decimal("0.00")

        # 4. PROCESS EACH ORDER LINE ITEM
        for item in order_data.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()

            unit_price_snapshot = product.selling_price
            quantity = item.quantity
            line_total = unit_price_snapshot * quantity

            total_order_amount += line_total

            db.add(models.OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price_snapshot
            ))

            # 🌟 NEW: consume from the oldest-expiring batch(es) first (FEFO), and use the
            # real weighted cost of what was actually sold instead of one blended cost figure.
            weighted_unit_cost = _consume_batches_fefo(db, product.id, quantity)
            product.current_quantity -= quantity

            db.add(models.StockTransaction(
                product_id=product.id,
                type="SALE",
                quantity_changed=-quantity,
                unit_cost=weighted_unit_cost,
                total_cost=quantity * weighted_unit_cost,
                notes=f"POS Sale (FEFO). Order ID: #{new_order.id}"
            ))

        # 5. ACCOUNTING & FINANCIAL LEDGER INTEGRATION
        new_order.total_amount = total_order_amount

        # 🌟 FIX: previously, overpaying (e.g. paying ₹500 cash on a ₹450 bill) recorded the
        # full ₹500 as income and silently dropped the ₹50 change owed. Now we cap what's
        # applied to the bill, log only the real revenue, and surface change_due explicitly.
        amount_applied = min(order_data.amount_paid, total_order_amount)
        change_due = order_data.amount_paid - amount_applied  # 0 unless overpaid
        pending_debt = total_order_amount - amount_applied

        credit_warning = None

        if pending_debt > 0:
            new_order.amount_pending = pending_debt
            if not order_data.customer_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A valid registered customer ID is required for Credit (Udhaar) or partial payments."
                )

            customer = db.query(models.Customer).filter(models.Customer.id == order_data.customer_id).first()
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Selected customer profile was not found."
                )

            # 🌟 NEW: Udhaar ceiling enforcement
            prospective_total_due = customer.total_credit_due + pending_debt
            if customer.credit_limit is not None and prospective_total_due > customer.credit_limit:
                if customer.credit_block_mode == "BLOCK":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Credit limit exceeded for {customer.name}. "
                            f"Limit: ₹{customer.credit_limit}, would-be balance: ₹{prospective_total_due}."
                        )
                    )
                else:
                    credit_warning = (
                        f"Warning: {customer.name} now exceeds their Udhaar limit "
                        f"(₹{prospective_total_due} / ₹{customer.credit_limit})."
                    )

            customer.total_credit_due = prospective_total_due

        if amount_applied > 0:
            db.add(models.FinanceLedger(
                type="INCOME",
                amount=amount_applied,
                category="SALES",
                is_automated=True,
                notes=f"POS Checkout Payment. Order Reference ID: #{new_order.id}"
            ))

        db.commit()

        response = {
            "status": "Success",
            "message": "Order processed successfully",
            "order_id": new_order.id,
            # 🌟 FIX: rounding explicitly to 2dp before the Decimal->float conversion that
            # JSON serialization requires, so we don't reintroduce float drift silently.
            "total_bill": round(float(total_order_amount), 2),
            "amount_paid": round(float(order_data.amount_paid), 2),
            "amount_pending": round(float(new_order.amount_pending), 2),
            "change_due": round(float(change_due), 2),  # 🌟 NEW field, additive only
        }
        if credit_warning:
            response["credit_warning"] = credit_warning  # 🌟 NEW field, additive only

        return response

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal database transaction failed: {str(e)}"
        )
