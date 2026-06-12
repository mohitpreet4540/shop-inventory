from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone  # 🌟 Modern timezone-aware imports
from app.database import Base


# 1. CATEGORY MODEL

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    subcategories = relationship("Category", backref="parent", remote_side=[id])
    products = relationship("Product", back_populates="category")



# 2. PRODUCT MODEL

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=False)
    brand = Column(String, index=True, default="Local")
    unit_type = Column(String, default="PIECE", nullable=False)
    
    cost_price = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    current_quantity = Column(Numeric(10, 2), default=0.00, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    category = relationship("Category", back_populates="products")


# 3. ORDER MODEL

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    
    total_amount = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0.00)
    amount_pending = Column(Numeric(10, 2), default=0.00)
    
    payment_method = Column(String, nullable=False) # CASH, ONLINE, PARTIAL, CREDIT
    payment_status = Column(String, default="PAID") # PAID, PARTIAL, UNPAID
    customer_info = Column(String, nullable=True)
    
    # 🌟 Fixed: Using lambda with timezone.utc to avoid the AttributeError
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    items = relationship("OrderItem", back_populates="order")



# 4. ORDER ITEM MODEL

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")



# 5. STOCK TRANSACTION MODEL

class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    type = Column(String, nullable=False)
    quantity_changed = Column(Numeric(10, 2), nullable=False)     
    
    # 🌟 Fixed: Standardizing timestamp logic
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(String, nullable=True)



# 6. FINANCE LEDGER MODEL

class FinanceLedger(Base):
    __tablename__ = "finance_ledger"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String, nullable=False)
    is_automated = Column(Boolean, default=True)
    
    # 🌟 Fixed: Standardizing timestamp logic
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(String, nullable=True)