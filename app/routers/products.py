from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Product, StockTransaction, Category
from app.schemas import (
    StockIncrementRequest, 
    ProductResponseSchema, 
    ProductCreateSchema, 
    ProductPriceUpdateSchema
)

router = APIRouter(prefix="/products", tags=["Products"])

# 1. LIST ALL PRODUCTS
@router.get("/", response_model=List[ProductResponseSchema])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


# 2. PRODUCT CREATION LOGIC
@router.post("/", response_model=ProductResponseSchema)
def create_product(product_data: ProductCreateSchema, db: Session = Depends(get_db)):
    category_exists = db.query(Category).filter(Category.id == product_data.category_id).first()
    if not category_exists:
        raise HTTPException(status_code=400, detail="Cannot add product. The specified category_id does not exist.")
    
    if product_data.barcode:
        duplicate_barcode = db.query(Product).filter(Product.barcode == product_data.barcode).first()
        if duplicate_barcode:
            raise HTTPException(
                status_code=400, 
                detail=f"Product setup failed. Barcode '{product_data.barcode}' is already assigned to '{duplicate_barcode.name}'."
            )
            
    try:
        new_product = Product(
            name=product_data.name, 
            brand=product_data.brand,           
            barcode=product_data.barcode,       
            unit_type=product_data.unit_type,   
            cost_price=product_data.cost_price,
            selling_price=product_data.selling_price, 
            current_quantity=product_data.current_quantity, 
            category_id=product_data.category_id
        )
        db.add(new_product)
        db.flush()  
        
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
        db.rollback()  
        raise HTTPException(status_code=500, detail=f"Product creation failed: {str(e)}")


# 3. STOCK REFILL LOGIC
@router.post("/add-stock/")
def add_product_stock(payload: StockIncrementRequest, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        product.current_quantity += payload.quantity
        
        if payload.cost_price is not None:
            product.cost_price = payload.cost_price
        
        if payload.selling_price is not None:
            product.selling_price = payload.selling_price
        
        stock_log = StockTransaction(
            product_id=product.id,
            quantity_changed=payload.quantity,
            type="RESTOCK",
            notes=payload.notes  
        )
        
        db.add(stock_log)
        db.commit()
        db.refresh(product)
        
        return {
            "status": "success",
            "message": f"Updated {product.name}: Added {payload.quantity} units. Rates updated if provided.",
            "updated_stock": product.current_quantity
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database transaction failed: {str(e)}")


# 4. PRICE UPDATE ENDPOINT
@router.put("/{product_id}/update-price", response_model=ProductResponseSchema)
def update_product_price(
    product_id: int, 
    price_data: ProductPriceUpdateSchema, 
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found.")
    
    try:
        old_selling = product.selling_price
        product.selling_price = price_data.selling_price
        if price_data.cost_price is not None:
            product.cost_price = price_data.cost_price
            
        audit_note = f"Price updated. Old Selling: ₹{old_selling} -> New: ₹{price_data.selling_price}"
        price_change_log = StockTransaction(
            product_id=product.id,
            quantity_changed=0,  
            type="PRICE_UPDATE",
            notes=audit_note
        )
        db.add(price_change_log)
        
        db.commit()
        db.refresh(product)
        return product
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to execute database price adjustment: {str(e)}")