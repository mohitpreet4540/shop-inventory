from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Product, StockTransaction, Category
from app.schemas import StockIncrementRequest, ProductResponseSchema, ProductCreateSchema

router = APIRouter(prefix="/products", tags=["Products"])

# 1. LIST ALL PRODUCTS
@router.get("/", response_model=List[ProductResponseSchema])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


# 2. YOUR PRODUCT CREATION LOGIC (INTEGRATED & POLISHED!)
@router.post("/", response_model=ProductResponseSchema)
def create_product(product_data: ProductCreateSchema, db: Session = Depends(get_db)):
    # Your exact check to verify category validity
    category_exists = db.query(Category).filter(Category.id == product_data.category_id).first()
    if not category_exists:
        raise HTTPException(status_code=400, detail="Cannot add product. The specified category_id does not exist.")
    
    try:
        # Your exact mapping logic
        new_product = Product(
            name=product_data.name, 
            cost_price=product_data.cost_price,
            selling_price=product_data.selling_price, 
            current_quantity=product_data.current_quantity,
            category_id=product_data.category_id
        )
        db.add(new_product)
        db.flush()  # Generates the product ID in memory first
        
        #  The Audit addition: If starting stock > 0, log it in history ledger!
        if new_product.current_quantity > 0:
            initial_stock_log = StockTransaction(
                product_id=new_product.id,
                quantity_changed=new_product.current_quantity,
                type="INITIAL_STOCK",
                notes="Initial inventory setup upon product creation"
            )
            db.add(initial_stock_log)
        
        db.commit()
        db.refresh(new_product)
        return new_product
        
    except Exception as e:
        db.rollback()  # Protects your database if a transaction fails
        raise HTTPException(status_code=500, detail=f"Product creation failed: {str(e)}")


# 3. STOCK REFILL LOGIC
@router.post("/add-stock/")
def add_product_stock(payload: StockIncrementRequest, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        product.current_quantity += payload.quantity
        
        stock_log = StockTransaction(
            product_id=product.id,
            quantity_changed=payload.quantity,
            type="RESTOCK",
            notes=payload.notes  # Uses your correct 'notes' column configuration
        )
        db.add(stock_log)
        db.commit()
        db.refresh(product)
        
        return {
            "status": "success",
            "message": f"Successfully added {payload.quantity} units to {product.name}",
            "updated_stock": product.current_quantity
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database transaction failed: {str(e)}")
    

    