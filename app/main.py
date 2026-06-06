from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel
import datetime

from app.database import engine, SessionLocal
from app.models import Base, Category, Product, Order, OrderItem, StockTransaction, FinanceLedger

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Universal Shop ERP Engine")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── PYDANTIC SCHEMAS ─────────────────────────────────────────────────

class CategoryCreateSchema(BaseModel):
    name: str
    parent_id: Optional[int] = None

class CategoryResponseSchema(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    class Config:
        from_attributes = True

class ProductCreateSchema(BaseModel):
    name: str
    cost_price: Decimal
    selling_price: Decimal
    current_quantity: int = 0
    category_id: int

class ProductResponseSchema(BaseModel):
    id: int
    name: str
    cost_price: Decimal
    selling_price: Decimal
    current_quantity: int
    category_id: int
    class Config:
        from_attributes = True

# New Checkout Schemas
class CartItemSchema(BaseModel):
    product_id: int
    quantity: int

class OrderCreateSchema(BaseModel):
    payment_method: str  # "CASH" or "ONLINE"
    items: List[CartItemSchema]

class OrderResponseSchema(BaseModel):
    id: int
    total_amount: Decimal
    payment_method: str
    payment_status: str
    timestamp: datetime.datetime
    class Config:
        from_attributes = True


@app.get("/")
def read_root():
    return {"status": "Online", "engine": "Universal Shop ERP"}


# ─── CATEGORY ENDPOINTS ───────────────────────────────────────────────

@app.post("/categories/", response_model=CategoryResponseSchema)
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

@app.get("/categories/", response_model=List[CategoryResponseSchema])
def get_all_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


# ─── PRODUCT ENDPOINTS ─────────────────────────────────────────────────

@app.post("/products/", response_model=ProductResponseSchema)
def create_product(product_data: ProductCreateSchema, db: Session = Depends(get_db)):
    category_exists = db.query(Category).filter(Category.id == product_data.category_id).first()
    if not category_exists:
        raise HTTPException(status_code=400, detail="Cannot add product. The specified category_id does not exist.")
    new_product = Product(
        name=product_data.name, cost_price=product_data.cost_price,
        selling_price=product_data.selling_price, current_quantity=product_data.current_quantity,
        category_id=product_data.category_id
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@app.get("/products/", response_model=List[ProductResponseSchema])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


# ─── CHECKOUT COUNTER ENDPOINTS (NEW!) ───────────────────────────────

@app.post("/orders/", response_model=OrderResponseSchema)
def checkout_cart(order_data: OrderCreateSchema, db: Session = Depends(get_db)):
    if not order_data.items:
        raise HTTPException(status_code=400, detail="Cart is completely empty.")

    running_total = Decimal("0.00")
    validated_items = []

    # Step 1: Run validation checks across all items in the shopping basket
    for cart_item in order_data.items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {cart_item.product_id} not found.")
        
        if product.current_quantity < cart_item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough stock for '{product.name}'. Available: {product.current_quantity}, Requested: {cart_item.quantity}"
            )
        
        # Calculate the price line item
        unit_price = Decimal(str(product.selling_price))
        item_total = unit_price * cart_item.quantity
        running_total += item_total
        validated_items.append((product, cart_item.quantity, unit_price))

    # Step 2: Save the Master Order details record
    db_order = Order(
        total_amount=running_total,
        payment_method=order_data.payment_method,
        payment_status="PAID"
    )
    db.add(db_order)
    db.flush()  # Generates the Order ID immediately without locking the transaction commit yet

    # Step 3: Loop through items, update inventory, and log to corresponding financial tables
    for product, qty, price in validated_items:
        # Deduct inventory count
        product.current_quantity -= qty
        
        # Save individual order receipt items
        db_item = OrderItem(order_id=db_order.id, product_id=product.id, quantity=qty, unit_price=price)
        db.add(db_item)

        # Log a record to the transaction history ledger
        db_tx = StockTransaction(product_id=product.id, type="SALE", quantity_changed=-qty, notes=f"Sold via Order #{db_order.id}")
        db.add(db_tx)

    # Step 4: Bookkeep incoming money straight into our Cash flow ledger
    db_finance = FinanceLedger(
        type="INCOME",
        amount=running_total,
        category="Customer Sale",
        is_automated=True,
        notes=f"Automated POS entry for Order #{db_order.id} via {order_data.payment_method}"
    )
    db.add(db_finance)

    db.commit()
    db.refresh(db_order)
    return db_order