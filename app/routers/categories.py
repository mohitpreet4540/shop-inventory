from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models import Category
from app.schemas import CategoryCreateSchema, CategoryResponseSchema

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("/", response_model=CategoryResponseSchema)
def create_category(category_data: CategoryCreateSchema, db: Session = Depends(get_db)):
    # 🌟 IMPROVEMENT 1: Standardize casing to Title Case (e.g., "groceries" -> "Groceries")
    clean_name = category_data.name.strip().title()

    # 🌟 IMPROVEMENT 2: Case-Insensitive Duplicate Prevention
    # Checks if a category with this exact name already exists in the database
    duplicate_check = db.query(Category).filter(func.lower(Category.name) == func.lower(clean_name)).first()
    if duplicate_check:
        raise HTTPException(
            status_code=400, 
            detail=f"Category '{clean_name}' already exists! Cannot create duplicate categories."
        )

    # Validate parent category validity if provided
    if category_data.parent_id:
        parent_exists = db.query(Category).filter(Category.id == category_data.parent_id).first()
        if not parent_exists:
            raise HTTPException(status_code=400, detail="The parent category you specified does not exist.")
            
    try:
        new_category = Category(name=clean_name, parent_id=category_data.parent_id)
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        return new_category
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create category: {str(e)}")

@router.get("/", response_model=List[CategoryResponseSchema])
def get_all_categories(db: Session = Depends(get_db)):
    # 🌟 BONUS IMPROVEMENT: Sort alphabetically so it looks clean on the shopkeeper's screen
    return db.query(Category).order_by(Category.name.asc()).all()