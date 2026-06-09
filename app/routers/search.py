from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from app.database import get_db
from app.models import Product
from app.schemas import ProductSearchResponseSchema

router = APIRouter(prefix="/search", tags=["Smart Search System"])

@router.get("/products/", response_model=List[ProductSearchResponseSchema])
def search_inventory(
    query: str = Query(..., description="Search by product name, brand, or barcode string"),
    db: Session = Depends(get_db)
):
   
    clean_query = query.strip()
    
    if not clean_query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
    
    try:
      
        search_results = db.query(Product).filter(
            or_(
                Product.name.ilike(f"%{clean_query}%"),
                Product.brand.ilike(f"%{clean_query}%"),
                Product.barcode == clean_query  # Exact match for barcode scans
            )
        ).limit(20).all() 
        return search_results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search engine execution failed: {str(e)}")