from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db  # 🌟 now importing the shared dependency instead of redefining it
from app.dependencies import get_current_user
from app import schemas, models

router = APIRouter(prefix="/api/search", tags=["Global Search Engine"])

# =================================================================
# GLOBAL INVENTORY PREVIEW SEARCH ENGINE (Any logged-in role)
# =================================================================
@router.get("/products", response_model=List[schemas.ProductSearchResponse])
def search_products(q: Optional[str] = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
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