from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import SessionLocal
from app import schemas, models

router = APIRouter(prefix="/api/search", tags=["Global Search Engine"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =================================================================
# GLOBAL INVENTORY PREVIEW SEARCH ENGINE
# =================================================================
@router.get("/products", response_model=List[schemas.ProductSearchResponse])
def search_products(q: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        # Return an empty list immediately if no search text is passed
        if not q:
            return []
            
        # Execute flexible lookup matching text against names, brands, or absolute barcodes
        results = db.query(models.Product).filter(
            (models.Product.name.ilike(f"%{q}%")) |
            (models.Product.brand.ilike(f"%{q}%")) |
            (models.Product.barcode == q)
        ).limit(20).all()  # Constrain limits so the dashboard UI drops down instantly
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Search Query Execution Failure: {str(e)}"
        )