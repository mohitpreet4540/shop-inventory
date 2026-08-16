from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app import models


def consume_batches_fefo(db: Session, product_id: int, quantity_needed: Decimal) -> Decimal:
    """
    Deducts `quantity_needed` from a product's stock batches, oldest-expiring first.
    Non-expiring batches (expiry_date IS NULL) are consumed last.
    Returns the weighted-average unit cost across whatever batches were drawn from.

    Used by both checkout (orders.py) and negative stock corrections (products.py) —
    any time stock leaves the shelf for a real (non-clerical) reason, it should go
    through FEFO so expiry accuracy and per-sale costing stay correct.
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Stock batch records are out of sync for product ID {product_id} "
                f"(short by {remaining_to_consume} units). Reconcile via a new restock entry."
            )
        )

    return total_cost / quantity_needed if quantity_needed > 0 else Decimal("0.00")
