from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import SessionLocal
from app import schemas, models

router = APIRouter(prefix="/api/products", tags=["Product Master Inventory"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =================================================================
# 1. CREATE PRODUCT (With Multi-Category Links & Initial Stock Audit)
# =================================================================
@router.post("/", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product_in: schemas.ProductCreate, db: Session = Depends(get_db)):
    try:
        # Prevent barcode duplication errors
        if product_in.barcode:
            existing = db.query(models.Product).filter(models.Product.barcode == product_in.barcode).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Inventory item with barcode {product_in.barcode} already exists as '{existing.name}'."
                )

        # Verify that all provided category IDs actually exist in the DB
        categories = db.query(models.Category).filter(models.Category.id.in_(product_in.category_ids)).all()
        if len(categories) != len(product_in.category_ids):
            raise HTTPException(
                status_code=404,
                detail="One or more specified Category IDs were not found in the database."
            )

        # Initialize the baseline product row
        new_product = models.Product(
            barcode=product_in.barcode,
            name=product_in.name,
            brand=product_in.brand,
            unit_type=product_in.unit_type,
            cost_price=product_in.cost_price,
            selling_price=product_in.selling_price,
            current_quantity=product_in.initial_stock,  # Assign initial stock baseline
            image_url=product_in.image_url,
            expiry_date=product_in.expiry_date
        )

        # Bind the category models through the junction relationship
        new_product.categories = categories
        db.add(new_product)
        db.flush()  # Extract the newly minted product ID safely

        # If day-one stock is injected, log an audit trail into the stock registry
        if product_in.initial_stock > 0:
            db.add(models.StockTransaction(
                product_id=new_product.id,
                type="INITIAL_STOCK",
                quantity_changed=product_in.initial_stock,
                unit_cost=product_in.cost_price,
                total_cost=product_in.initial_stock * product_in.cost_price,
                notes="System startup inventory baseline assignment."
            ))

        db.commit()
        db.refresh(new_product)
        return new_product

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database Write Failure: {str(e)}")


# =================================================================
# 2. MASTER INVENTORY LEDGER (🔄 Step 1.3: Dual-Sieve Filtering Suite)
# =================================================================
@router.get("/", response_model=List[schemas.ProductResponse])
def list_inventory_ledger(
    search: Optional[str] = None,
    brand: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)

    # Filter Sieve A: Dynamic Category Junction Join
    if category_id:
        query = query.join(models.Product.categories).filter(models.Category.id == category_id)

    # Filter Sieve B: Direct Brand Match
    if brand:
        query = query.filter(models.Product.brand.ilike(f"%{brand}%"))

    # Filter Sieve C: Text Search (Matches Name or Barcode)
    if search:
        query = query.filter(
            (models.Product.name.ilike(f"%{search}%")) |
            (models.Product.barcode == search)
        )

    return query.order_by(models.Product.name.asc()).all()


# =================================================================
# 3. LIVE BARCODE LOOKUP PATH
# =================================================================
@router.get("/lookup/{barcode}", response_model=schemas.ProductResponse)
def lookup_by_barcode(barcode: str, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.barcode == barcode).first()
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Barcode {barcode} does not exist in local inventory logs."
        )
    return product


# =================================================================
# 4. PRICE ENGINE MODIFICATION ENDPOINT
# =================================================================
@router.patch("/{product_id}/price", response_model=schemas.ProductResponse)
def update_product_pricing(
    product_id: int, 
    pricing_updates: schemas.ProductPriceUpdate, 
    db: Session = Depends(get_db)
):
    try:
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Target inventory item not found.")

        # Extract values for safe validation comparison
        target_cost = pricing_updates.cost_price if pricing_updates.cost_price is not None else product.cost_price
        target_sale = pricing_updates.selling_price

        # Safeguard margins from accidental retail human error
        if target_sale < target_cost:
            raise HTTPException(
                status_code=400,
                detail=f"Margin Violation: Selling price (₹{target_sale}) cannot run lower than cost (₹{target_cost})."
            )

        # Commit updates
        product.selling_price = target_sale
        if pricing_updates.cost_price is not None:
            product.cost_price = pricing_updates.cost_price

        # Log changes into the audit trail ledger
        db.add(models.StockTransaction(
            product_id=product.id,
            type="PRICE_UPDATE",
            quantity_changed=0,
            notes=f"Pricing manually updated to Cost: ₹{target_cost} | Sale: ₹{target_sale}"
        ))

        db.commit()
        db.refresh(product)
        return product

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Pricing Migration failure: {str(e)}")
    

# Append this endpoint to app/routers/products.py

@router.patch("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int, 
    product_update: schemas.ProductUpdate, 
    db: Session = Depends(get_db)
):
    try:
        # 1. Verify the product exists
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Target product not found.")

        # 2. Extract only the fields explicitly sent by the client frontend
        update_data = product_update.model_dump(exclude_unset=True)

        # 3. Validation: Prevent duplicate barcodes across different products
        if "barcode" in update_data and update_data["barcode"]:
            existing = db.query(models.Product).filter(
                models.Product.barcode == update_data["barcode"],
                models.Product.id != product_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Barcode '{update_data['barcode']}' is already assigned to another item ('{existing.name}')."
                )

        # 4. Validation: Safeguard profit margins against human input error
        new_cost = update_data.get("cost_price", product.cost_price)
        new_sale = update_data.get("selling_price", product.selling_price)
        if new_sale < new_cost:
            raise HTTPException(
                status_code=400,
                detail=f"Margin Violation: Selling price (₹{new_sale}) cannot run lower than cost price (₹{new_cost})."
            )

        # 5. Handle Relational Updates: Many-to-Many Categories Link
        if "category_ids" in update_data:
            category_ids = update_data.pop("category_ids")
            categories = db.query(models.Category).filter(models.Category.id.in_(category_ids)).all()
            if len(categories) != len(category_ids):
                raise HTTPException(status_code=404, detail="One or more specified Category IDs do not exist.")
            product.categories = categories

        # 6. Apply all other standard column updates dynamically
        price_changed = False
        for key, value in update_data.items():
            if key in ["cost_price", "selling_price"] and getattr(product, key) != value:
                price_changed = True
            setattr(product, key, value)

        # 7. Audit Logging: If pricing changed, append an automated tracking log entry
        if price_changed:
            db.add(models.StockTransaction(
                product_id=product.id,
                type="PRICE_UPDATE",
                quantity_changed=0,
                unit_cost=product.cost_price,
                total_cost=0,
                notes=f"System Update: Base inventory item structural recalculation."
            ))

        db.commit()
        db.refresh(product)
        return product

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to execute product structural update: {str(e)}")
    
# =================================================================
# 5. WHOLESALE PROCUREMENT INGESTION SYSTEM (RESTOCK ROUTE)
# =================================================================
@router.post("/{product_id}/restock", status_code=status.HTTP_200_OK)
def restock_product(
    product_id: int, 
    payload: schemas.ProductRestock, 
    db: Session = Depends(get_db)
):
    try:
        # 1. Locate the product and lock the row to avoid overlapping checkout deductions
        product = db.query(models.Product).filter(models.Product.id == product_id).with_for_update().first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Product with ID {product_id} does not exist in inventory."
            )

        # Calculate the total out-of-pocket acquisition cost
        total_acquisition_cost = payload.quantity * payload.unit_cost

        # 2. Update stock quantities and update product's active purchase cost
        product.current_quantity += payload.quantity
        product.cost_price = payload.unit_cost

        # 3. Record a RESTOCK log entry in the audit transaction database
        db.add(models.StockTransaction(
            product_id=product.id,
            type="RESTOCK",
            quantity_changed=payload.quantity,
            unit_cost=payload.unit_cost,
            total_cost=total_acquisition_cost,
            notes=payload.notes or f"Wholesale delivery arrival. New cost: ₹{payload.unit_cost}/unit."
        ))

        # 4. Automate double-entry accounting: Record as an EXPENSE in the FinanceLedger
        db.add(models.FinanceLedger(
            type="EXPENSE",
            amount=total_acquisition_cost,
            category="ACQUISITION",
            is_automated=True,
            notes=f"Auto-generated: Wholesale acquisition of {payload.quantity} units of '{product.name}' (ID: {product.id})."
        ))

        # 5. Commit all relational changes atomically
        db.commit()
        db.refresh(product)

        return {
            "status": "Success",
            "message": f"Successfully processed incoming supply of {payload.quantity} units.",
            "product_name": product.name,
            "new_on_hand_quantity": product.current_quantity,
            "updated_cost_price": product.cost_price,
            "expense_logged": total_acquisition_cost
        }

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Wholesale procurement transaction failed: {str(e)}"
        )