from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import SessionLocal
from app import schemas, models

router = APIRouter(prefix="/api/reports", tags=["Audit Reports & Ledgers"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =================================================================
# FETCH STOCK TRANSACTION AUDIT TRAILS
# =================================================================
@router.get("/stock-ledger", response_model=List[schemas.StockTransactionResponse])
def get_stock_ledger_report(
    product_id: Optional[int] = None,
    transaction_type: Optional[str] = None,  # SALE, INITIAL_STOCK, PRICE_UPDATE, RESTOCK
    db: Session = Depends(get_db)
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