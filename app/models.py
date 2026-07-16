from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Boolean, Table, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

# =================================================================
# MANY-TO-MANY JUNCTION TABLE
# =================================================================
product_category_links = Table(
    "product_category_links",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)
)

# =================================================================
# 1. THE CUSTOMER PROFILE MODEL (Integrated Debt Ledger)
# =================================================================
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    total_credit_due = Column(Numeric(10, 2), default=0.00, nullable=False) # Total running udhaar balance outstanding
    date_registered = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Link back to all orders made by this person
    orders = relationship("Order", back_populates="customer")


# =================================================================
# 2. THE CATEGORY MODEL (With soft-delete capability tracking)
# =================================================================
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Many-to-Many relationship mapping
    products = relationship("Product", secondary=product_category_links, back_populates="categories")


# =================================================================
# 3. THE PRODUCT MODEL (Fully Complete & Relinked)
# =================================================================
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String, default="Local")
    barcode = Column(String, unique=True, nullable=True, index=True)
    unit_type = Column(String, default="PIECE")
    cost_price = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    current_quantity = Column(Numeric(10, 2), default=0.00)
    image_url = Column(String, nullable=True)
    expiry_date = Column(Date, nullable=True)
    
    # Ensures no AttributeError on 'datetime' class lookup
    date_added = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Many-to-Many Layout Link
    categories = relationship("Category", secondary=product_category_links, back_populates="products")
    
    # 🌟 CRITICAL FIX: Add these missing bi-directional mapping hooks
    order_items = relationship("OrderItem", back_populates="product")
    transactions = relationship("StockTransaction", back_populates="product")

# =================================================================
# 4. THE ORDER MODEL (Structured Link to Customer Profile)
# =================================================================
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0.00)
    amount_pending = Column(Numeric(10, 2), default=0.00)
    
    payment_method = Column(String, nullable=False)  # CASH, ONLINE, PARTIAL, CREDIT
    payment_status = Column(String, default="PAID")   # PAID, PARTIAL, UNPAID
    
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_info = Column(String, nullable=True)      # Fallback legacy text field tracking

    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


# =================================================================
# 5. THE ORDER ITEM MODEL (Fully Complete)
# =================================================================
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# =================================================================
# 6. UNIFIED STOCK TRANSACTION LEDGER MODEL (Fully Complete)
# =================================================================
class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)                 # INITIAL_STOCK, RESTOCK, SALE, PRICE_UPDATE
    quantity_changed = Column(Numeric(10, 2), nullable=False)     
    
    unit_cost = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_cost = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(String, nullable=True)

    product = relationship("Product", back_populates="transactions")


# =================================================================
# 7. THE FINANCE LEDGER MODEL (Fully Complete)
# =================================================================
class FinanceLedger(Base):
    __tablename__ = "finance_ledger"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)     # INCOME, EXPENSE
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String, nullable=False) # SALES, ACQUISITION, REFUND, DEBT_REPAYMENT
    is_automated = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(String, nullable=True)