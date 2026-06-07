from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Category
from app.schemas import CategoryCreateSchema, CategoryResponseSchema

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("/", response_model=CategoryResponseSchema)
def create_category(category_data: CategoryCreateSchema, db: Session = Depends(get_db)):
    if category_data.parent_id:
        parent_exists = db.query(Category).filter(Category.id == category_data.parent_id).first()
        if not parent_exists:
            raise HTTPException(status_code=400, detail="The parent category you specified does not exist.")
            
    new_category = Category(name=category_data.name, parent_id=category_data.parent_id)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/", response_model=List[CategoryResponseSchema])
def get_all_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()