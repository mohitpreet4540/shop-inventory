from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app.models import StockTransaction, Product
from app.schemas import StockTransactionResponseSchema

router = APIRouter(prefix="/reports", tags=["Reports & Audit Ledgers"])

@router.get("/stock-ledger/", response_model=List[StockTransactionResponseSchema])
def get_stock_ledger(
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type: INITIAL_STOCK, RESTOCK, SALE"),
    db: Session = Depends(get_db)
):
    try:
        # Step 1: Core query joining StockTransaction with Product to pull names efficiently
        query = db.query(
            StockTransaction.id,
            StockTransaction.product_id,
            Product.name.label("product_name"),
            StockTransaction.quantity_changed,
            StockTransaction.type,
            StockTransaction.notes,
            StockTransaction.timestamp
        ).join(Product, StockTransaction.product_id == Product.id)
        
        # Step 2: Apply dynamic filter if the shopkeeper selects a specific type
        if transaction_type:
            query = query.filter(func.upper(StockTransaction.type) == transaction_type.upper())
            
        # Step 3: Sort chronologically so the newest transaction is at the very top
        ledger_entries = query.order_by(StockTransaction.timestamp.desc()).all()
        
        return ledger_entries

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load ledger history: {str(e)}")