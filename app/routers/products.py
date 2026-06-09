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


# 2. PRODUCT CREATION LOGIC (WITH BRAND, BARCODE, AND UNIT TYPE MAPPINGS)
@router.post("/", response_model=ProductResponseSchema)
def create_product(product_data: ProductCreateSchema, db: Session = Depends(get_db)):
    # Verify category validity
    category_exists = db.query(Category).filter(Category.id == product_data.category_id).first()
    if not category_exists:
        raise HTTPException(status_code=400, detail="Cannot add product. The specified category_id does not exist.")
    
    # Optional Protection: Prevent creating duplicate active barcodes if scanned by mistake
    if product_data.barcode:
        duplicate_barcode = db.query(Product).filter(Product.barcode == product_data.barcode).first()
        if duplicate_barcode:
            raise HTTPException(
                status_code=400, 
                detail=f"Product setup failed. Barcode '{product_data.barcode}' is already assigned to '{duplicate_barcode.name}'."
            )
            
    try:
        # 🌟 Unpacking brand, barcode, and unit_type values into the DB engine
        new_product = Product(
            name=product_data.name, 
            brand=product_data.brand,           # 👈 Injected brand section mapping
            barcode=product_data.barcode,       # 👈 Injected physical barcode registry mapping
            unit_type=product_data.unit_type,   # 👈 Injected unit selection mapping (KG, METER, PIECE)
            cost_price=product_data.cost_price,
            selling_price=product_data.selling_price, 
            current_quantity=product_data.current_quantity, # 🌟 Safely registers incoming Decimal weights
            category_id=product_data.category_id
        )
        db.add(new_product)
        db.flush()  # Generates the product ID in memory first
        
        # The Audit addition: If starting stock > 0, log it in history ledger!
        if new_product.current_quantity > 0:
            initial_stock_log = StockTransaction(
                product_id=new_product.id,
                quantity_changed=new_product.current_quantity, # Logs fractional decimal setups cleanly
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


# 3. STOCK REFILL LOGIC (DECIMAL COMPATIBLE)

@router.post("/add-stock/")
def add_product_stock(payload: StockIncrementRequest, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        # Update Quantity
        product.current_quantity += payload.quantity
        
        #  prices ONLY if provided in the request
        if payload.cost_price is not None:
            product.cost_price = payload.cost_price
        
        if payload.selling_price is not None:
            product.selling_price = payload.selling_price
        
        # Log Transaction
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