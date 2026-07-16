from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import SessionLocal
from app import schemas, models

router = APIRouter(prefix="/api/categories", tags=["Category Tree Management"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =================================================================
# 1. CREATE CATEGORY OR SUBCATEGORY
# =================================================================
@router.post("/", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category_data: schemas.CategoryCreate, db: Session = Depends(get_db)):
    try:
        # If a parent_id is provided, verify it points to a real category
        if category_data.parent_id:
            parent = db.query(models.Category).filter(models.Category.id == category_data.parent_id).first()
            if not parent:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Parent category with ID {category_data.parent_id} does not exist."
                )
            
            # Enforce a shallow 2-level limit: Subcategories cannot become parents
            if parent.parent_id is not None:
                raise HTTPException(
                    status_code=400,
                    detail="Deep nesting blocked. You can only attach subcategories to primary parent categories."
                )

        new_category = models.Category(
            name=category_data.name,
            parent_id=category_data.parent_id,
            is_active=True
        )
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        return new_category

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database Insertion Error: {str(e)}")

# =================================================================
# 2. FETCH REAL-TIME HIERARCHICAL TREE (With live product counters)
# =================================================================
@router.get("/tree", response_model=List[schemas.CategoryTreeResponse])
def get_category_tree(db: Session = Depends(get_db)):
    # Pull all categories out of the database
    categories = db.query(models.Category).all()
    
    # Calculate product metrics dynamically using the junction table
    counts_query = db.query(
        models.product_category_links.c.category_id,
        func.count(models.product_category_links.c.product_id).label("total")
    ).group_by(models.product_category_links.c.category_id).all()
    
    # Convert counts mapping into a fast-lookup Python dictionary
    product_counts = {cat_id: count for cat_id, count in counts_query}

    # Step A: Transform rows into dictionary structures containing the product counts
    nodes = {}
    for cat in categories:
        nodes[cat.id] = {
            "id": cat.id,
            "name": cat.name,
            "parent_id": cat.parent_id,
            "is_active": cat.is_active,
            "product_count": product_counts.get(cat.id, 0),
            "subcategories": []
        }

    # Step B: Assemble the tree hierarchy by mapping children straight to parents
    root_nodes = []
    for cat_id, node in nodes.items():
        parent_id = node["parent_id"]
        if parent_id is None:
            # This is a master tier parent category
            root_nodes.append(node)
        else:
            # This is a subcategory; append it into the parent's nested layout array
            if parent_id in nodes:
                nodes[parent_id]["subcategories"].append(node)
                
    return root_nodes

# =================================================================
# 3. SAFE SOFT-INACTIVATION TOGGLE (No hard deletion)
# =================================================================
@router.patch("/{category_id}/toggle", response_model=schemas.CategoryResponse)
def toggle_category_status(category_id: int, db: Session = Depends(get_db)):
    try:
        category = db.query(models.Category).filter(models.Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Target category profile not found.")

        # Flip the binary state switch
        category.is_active = not category.is_active
        
        # Cascading protection rules: If a parent is deactivated, automatically deactivate its children
        if not category.is_active and category.parent_id is None:
            db.query(models.Category).filter(models.Category.parent_id == category.id).update(
                {"is_active": False}
            )

        db.commit()
        db.refresh(category)
        return category

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Status Change Transaction Failure: {str(e)}")