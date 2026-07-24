import csv
import io
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app.dependencies import require_roles, get_current_user
from app import schemas, models

router = APIRouter(prefix="/api/products", tags=["Product Master Inventory"])


# =================================================================
# 1. CREATE PRODUCT (OWNER, ADMIN)
# =================================================================
@router.post("/", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN")),
):
    try:
        if product_in.barcode:
            existing = db.query(models.Product).filter(models.Product.barcode == product_in.barcode).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Inventory item with barcode {product_in.barcode} already exists as '{existing.name}'."
                )

        categories = db.query(models.Category).filter(models.Category.id.in_(product_in.category_ids)).all()
        if len(categories) != len(product_in.category_ids):
            raise HTTPException(
                status_code=404,
                detail="One or more specified Category IDs were not found in the database."
            )

        new_product = models.Product(
            barcode=product_in.barcode,
            name=product_in.name,
            brand=product_in.brand,
            unit_type=product_in.unit_type,
            cost_price=product_in.cost_price,
            selling_price=product_in.selling_price,
            current_quantity=product_in.initial_stock,
            image_url=product_in.image_url,
            expiry_date=product_in.expiry_date
        )

        new_product.categories = categories
        db.add(new_product)
        db.flush()

        if product_in.initial_stock > 0:
            db.add(models.StockTransaction(
                product_id=new_product.id,
                type="INITIAL_STOCK",
                quantity_changed=product_in.initial_stock,
                unit_cost=product_in.cost_price,
                total_cost=product_in.initial_stock * product_in.cost_price,
                notes="System startup inventory baseline assignment."
            ))
            # 🌟 NEW: also register this as a trackable batch so FEFO checkout logic has something to consume
            db.add(models.StockBatch(
                product_id=new_product.id,
                quantity_received=product_in.initial_stock,
                quantity_remaining=product_in.initial_stock,
                unit_cost=product_in.cost_price,
                expiry_date=product_in.expiry_date,
                notes="Initial stock batch."
            ))

        db.commit()
        db.refresh(new_product)
        return new_product

    except HTTPException as he:
        db.rollback()
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Inventory item with barcode {product_in.barcode} already exists (concurrent write detected)."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database Write Failure: {str(e)}")


# =================================================================
# 2. MASTER INVENTORY LEDGER (Any logged-in role)
# =================================================================
@router.get("/", response_model=List[schemas.ProductResponse])
def list_inventory_ledger(
    search: Optional[str] = None,
    brand: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Product)

    if category_id:
        query = query.join(models.Product.categories).filter(models.Category.id == category_id)

    if brand:
        query = query.filter(models.Product.brand.ilike(f"%{brand}%"))

    if search:
        query = query.filter(
            (models.Product.name.ilike(f"%{search}%")) |
            (models.Product.barcode == search)
        )

    return query.order_by(models.Product.name.asc()).all()


# =================================================================
# 3. LIVE BARCODE LOOKUP PATH (Any logged-in role — needed at checkout)
# =================================================================
@router.get("/lookup/{barcode}", response_model=schemas.ProductResponse)
def lookup_by_barcode(barcode: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    product = db.query(models.Product).filter(models.Product.barcode == barcode).first()
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Barcode {barcode} does not exist in local inventory logs."
        )
    return product


# =================================================================
# 4. PRICE ENGINE MODIFICATION ENDPOINT (OWNER, ADMIN)
# =================================================================
@router.patch("/{product_id}/price", response_model=schemas.ProductResponse)
def update_product_pricing(
    product_id: int,
    pricing_updates: schemas.ProductPriceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN")),
):
    try:
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Target inventory item not found.")

        target_cost = pricing_updates.cost_price if pricing_updates.cost_price is not None else product.cost_price
        target_sale = pricing_updates.selling_price

        if target_sale < target_cost:
            raise HTTPException(
                status_code=400,
                detail=f"Margin Violation: Selling price (₹{target_sale}) cannot run lower than cost (₹{target_cost})."
            )

        product.selling_price = target_sale
        if pricing_updates.cost_price is not None:
            product.cost_price = pricing_updates.cost_price

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


@router.patch("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN")),
):
    try:
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Target product not found.")

        update_data = product_update.model_dump(exclude_unset=True)

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

        new_cost = update_data.get("cost_price", product.cost_price)
        new_sale = update_data.get("selling_price", product.selling_price)
        if new_sale < new_cost:
            raise HTTPException(
                status_code=400,
                detail=f"Margin Violation: Selling price (₹{new_sale}) cannot run lower than cost price (₹{new_cost})."
            )

        if "category_ids" in update_data:
            category_ids = update_data.pop("category_ids")
            categories = db.query(models.Category).filter(models.Category.id.in_(category_ids)).all()
            if len(categories) != len(category_ids):
                raise HTTPException(status_code=404, detail="One or more specified Category IDs do not exist.")
            product.categories = categories

        price_changed = False
        for key, value in update_data.items():
            if key in ["cost_price", "selling_price"] and getattr(product, key) != value:
                price_changed = True
            setattr(product, key, value)

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
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Update conflicts with an existing record (e.g. duplicate barcode).")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to execute product structural update: {str(e)}")

# =================================================================
# 5. WHOLESALE PROCUREMENT INGESTION SYSTEM (RESTOCK ROUTE) (OWNER, ADMIN)
# =================================================================
@router.post("/{product_id}/restock", status_code=status.HTTP_200_OK)
def restock_product(
    product_id: int,
    payload: schemas.ProductRestock,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN")),
):
    try:
        product = db.query(models.Product).filter(models.Product.id == product_id).with_for_update().first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} does not exist in inventory."
            )

        total_acquisition_cost = payload.quantity * payload.unit_cost

        product.current_quantity += payload.quantity
        product.cost_price = payload.unit_cost

        db.add(models.StockTransaction(
            product_id=product.id,
            type="RESTOCK",
            quantity_changed=payload.quantity,
            unit_cost=payload.unit_cost,
            total_cost=total_acquisition_cost,
            notes=payload.notes or f"Wholesale delivery arrival. New cost: ₹{payload.unit_cost}/unit."
        ))

        # 🌟 NEW: each restock is its own batch with its own expiry_date — this is what makes
        # FEFO (First-Expiry-First-Out) checkout deduction possible instead of one blended number.
        db.add(models.StockBatch(
            product_id=product.id,
            quantity_received=payload.quantity,
            quantity_remaining=payload.quantity,
            unit_cost=payload.unit_cost,
            expiry_date=payload.expiry_date,
            notes=payload.notes or "Restock batch."
        ))

        db.add(models.FinanceLedger(
            type="EXPENSE",
            amount=total_acquisition_cost,
            category="ACQUISITION",
            is_automated=True,
            notes=f"Auto-generated: Wholesale acquisition of {payload.quantity} units of '{product.name}' (ID: {product.id})."
        ))

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


# =================================================================
# 🌟 NEW: VIEW A PRODUCT'S BATCHES (Any logged-in role)
# =================================================================
@router.get("/{product_id}/batches", response_model=List[schemas.StockBatchResponse])
def list_product_batches(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    # Oldest-expiring batches first (non-perishable / no-expiry batches sort last)
    return db.query(models.StockBatch).filter(
        models.StockBatch.product_id == product_id
    ).order_by(
        models.StockBatch.expiry_date.is_(None),
        models.StockBatch.expiry_date.asc()
    ).all()


# =================================================================
# 6. 🌟 NEW: BULK IMPORT VIA CSV (OWNER, ADMIN)
# =================================================================
# Expected CSV columns (header row required):
#   name*, cost_price*, selling_price*, brand, barcode, unit_type,
#   initial_stock, category_names (semicolon-separated, auto-created if missing),
#   image_url
# * = required columns
@router.post("/bulk-import", status_code=status.HTTP_200_OK)
async def bulk_import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN")),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported for bulk import.")

    raw = await file.read()
    try:
        text_data = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please save your CSV as UTF-8.")

    reader = csv.DictReader(io.StringIO(text_data))
    required_columns = {"name", "cost_price", "selling_price"}
    found_columns = set(c.strip() for c in (reader.fieldnames or []))
    if not required_columns.issubset(found_columns):
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing required columns. Required: {sorted(required_columns)}. Found: {sorted(found_columns)}"
        )

    created, skipped, errors = [], [], []

    # Cache existing categories by lowercase name to avoid duplicate creation within this import
    category_cache = {c.name.strip().lower(): c for c in db.query(models.Category).all()}

    for row_num, row in enumerate(reader, start=2):  # row 1 is the header
        try:
            name = (row.get("name") or "").strip()
            if not name:
                errors.append({"row": row_num, "reason": "Missing product name."})
                continue

            barcode = (row.get("barcode") or "").strip() or None
            if barcode:
                existing_product = db.query(models.Product).filter(models.Product.barcode == barcode).first()
                if existing_product:
                    skipped.append({"row": row_num, "reason": f"Barcode {barcode} already exists as '{existing_product.name}'."})
                    continue

            try:
                cost_price = Decimal(str(row["cost_price"]).strip())
                selling_price = Decimal(str(row["selling_price"]).strip())
            except (InvalidOperation, KeyError):
                errors.append({"row": row_num, "reason": "cost_price / selling_price must be valid numbers."})
                continue

            if selling_price < cost_price:
                errors.append({"row": row_num, "reason": "Selling price cannot be lower than cost price."})
                continue

            try:
                initial_stock = Decimal(str(row.get("initial_stock") or "0").strip() or "0")
            except InvalidOperation:
                errors.append({"row": row_num, "reason": "initial_stock must be a valid number."})
                continue

            # Resolve or auto-create categories (semicolon-separated names)
            category_names = [c.strip() for c in (row.get("category_names") or "").split(";") if c.strip()]
            resolved_categories = []
            for cat_name in category_names:
                key = cat_name.lower()
                if key not in category_cache:
                    new_cat = models.Category(name=cat_name, is_active=True)
                    db.add(new_cat)
                    db.flush()
                    category_cache[key] = new_cat
                resolved_categories.append(category_cache[key])

            new_product = models.Product(
                name=name,
                brand=(row.get("brand") or "Local").strip() or "Local",
                barcode=barcode,
                unit_type=(row.get("unit_type") or "PIECE").strip() or "PIECE",
                cost_price=cost_price,
                selling_price=selling_price,
                current_quantity=initial_stock,
                image_url=(row.get("image_url") or "").strip() or None,
                categories=resolved_categories,
            )
            db.add(new_product)
            db.flush()

            if initial_stock > 0:
                db.add(models.StockTransaction(
                    product_id=new_product.id,
                    type="INITIAL_STOCK",
                    quantity_changed=initial_stock,
                    unit_cost=cost_price,
                    total_cost=initial_stock * cost_price,
                    notes="Bulk import baseline assignment.",
                ))

            created.append({"row": row_num, "name": name})

        except Exception as e:
            errors.append({"row": row_num, "reason": f"Unexpected error: {str(e)}"})
            continue

    db.commit()

    return {
        "status": "Completed",
        "created_count": len(created),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "created": created,
        "skipped": skipped,
        "errors": errors,
    }
