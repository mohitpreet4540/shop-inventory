from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from app.database import get_db  # 🌟 now importing the shared dependency instead of redefining it
from app.dependencies import require_roles, get_current_user
from app import schemas, models

router = APIRouter(prefix="/api/reports", tags=["Audit Reports & Ledgers"])

# =================================================================
# FETCH STOCK TRANSACTION AUDIT TRAILS (OWNER, ADMIN only)
# =================================================================
@router.get("/stock-ledger", response_model=List[schemas.StockTransactionResponse])
def get_stock_ledger_report(
    product_id: Optional[int] = None,
    transaction_type: Optional[str] = None,  # SALE, INITIAL_STOCK, PRICE_UPDATE, RESTOCK
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN")),
):
    try:
        # Base query joining the stock ledger with the product master table
        query = db.query(models.StockTransaction)
        
        # Filter by specific product if selected
        if product_id:
            query = query.filter(models.StockTransaction.product_id == product_id)
            
        # Filter by action type configuration parameters
        if transaction_type:
            query = query.filter(models.StockTransaction.type == transaction_type)
            
        # Sort history sequentially so newest updates appear at the top
        transactions = query.order_by(models.StockTransaction.timestamp.desc()).all()
        
        report_data = []
        for tx in transactions:
            # Safe fallback if relationship lookup isn't fully cached
            product_name = tx.product.name if getattr(tx, "product", None) else "Archived Product"
            
            report_data.append(
                schemas.StockTransactionResponse(
                    id=tx.id,
                    product_id=tx.product_id,
                    product_name=product_name,
                    quantity_changed=tx.quantity_changed,
                    type=tx.type,
                    unit_cost=tx.unit_cost,
                    total_cost=tx.total_cost,
                    notes=tx.notes,
                    timestamp=tx.timestamp
                )
            )
            
        return report_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate stock auditing trail records: {str(e)}"
        )


# =================================================================
# 🌟 NEW: EXPIRING SOON — batch-level alert list (Any logged-in role)
# =================================================================
@router.get("/expiring-soon", response_model=List[schemas.ExpiringBatchAlert])
def get_expiring_soon(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        today = datetime.date.today()
        cutoff = today + datetime.timedelta(days=days)

        batches = db.query(models.StockBatch).filter(
            models.StockBatch.quantity_remaining > 0,
            models.StockBatch.expiry_date.isnot(None),
            models.StockBatch.expiry_date <= cutoff,
        ).order_by(models.StockBatch.expiry_date.asc()).all()

        alerts = []
        for batch in batches:
            product_name = batch.product.name if getattr(batch, "product", None) else "Archived Product"
            alerts.append(schemas.ExpiringBatchAlert(
                batch_id=batch.id,
                product_id=batch.product_id,
                product_name=product_name,
                quantity_remaining=batch.quantity_remaining,
                expiry_date=batch.expiry_date,
                days_until_expiry=(batch.expiry_date - today).days,
            ))

        return alerts

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate expiring-stock report: {str(e)}"
        )