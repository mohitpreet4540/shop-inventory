from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from decimal import Decimal
import datetime

# ==========================================
# 0. AUTH & USER SCHEMAS
# ==========================================
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, description="Minimum 6 characters")
    role: str = Field(default="CASHIER", description="OWNER, ADMIN, or CASHIER")

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


# ==========================================
# 1. CATEGORY MANAGEMENT SCHEMAS
# ==========================================
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the category")
    parent_id: Optional[int] = Field(None, description="ID of parent category if this is a subcategory")

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    parent_id: Optional[int] = None

class CategorySimpleResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CategoryResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True

class CategoryTreeResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    is_active: bool
    product_count: int
    subcategories: List["CategoryTreeResponse"] = []

    class Config:
        from_attributes = True


# ==========================================
# 2. PRODUCT MASTER DATA SCHEMAS
# ==========================================
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the item")
    brand: Optional[str] = "Local"
    barcode: Optional[str] = None
    unit_type: Optional[str] = "PIECE"
    cost_price: Decimal = Field(..., gt=0, description="Wholesale procurement cost price")
    selling_price: Decimal = Field(..., gt=0, description="Retail selling price charged to customer")
    initial_stock: Decimal = Field(default=Decimal("0.00"), ge=0, description="Starting quantity of item")
    category_ids: List[int] = Field(..., min_items=1, description="List of category IDs this product belongs to")
    image_url: Optional[str] = None
    expiry_date: Optional[datetime.date] = None

    @model_validator(mode="after")
    def verify_pricing_margins(self) -> "ProductCreate":
        if self.selling_price < self.cost_price:
            raise ValueError("Operational Mismatch: Selling price cannot be lower than wholesale cost price.")
        return self

class ProductResponse(BaseModel):
    id: int
    name: str
    brand: str
    barcode: Optional[str] = None
    unit_type: str
    cost_price: Decimal
    selling_price: Decimal
    current_quantity: Decimal
    image_url: Optional[str] = None
    expiry_date: Optional[datetime.date] = None
    date_added: datetime.datetime
    categories: List[CategorySimpleResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True

class ProductSearchResponse(BaseModel):
    id: int
    name: str
    brand: str
    barcode: Optional[str] = None
    unit_type: str
    selling_price: Decimal
    current_quantity: Decimal

    class Config:
        from_attributes = True

class ProductPriceUpdate(BaseModel):
    selling_price: Decimal = Field(..., gt=0)
    cost_price: Optional[Decimal] = Field(None, gt=0)

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    brand: Optional[str] = None
    barcode: Optional[str] = None
    unit_type: Optional[str] = None
    cost_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    current_quantity: Optional[Decimal] = None
    image_url: Optional[str] = None
    expiry_date: Optional[datetime.date] = None
    category_ids: Optional[List[int]] = None

    class Config:
        from_attributes = True

class ProductRestock(BaseModel):
    quantity: Decimal = Field(..., gt=0, description="Incoming wholesale stock quantity")
    unit_cost: Decimal = Field(..., ge=0, description="Actual supplier cost price per individual unit")
    expiry_date: Optional[datetime.date] = Field(None, description="Expiry date for THIS specific batch, if perishable")
    notes: Optional[str] = Field(None, max_length=255, description="Optional invoice numbers or delivery notes")

    class Config:
        from_attributes = True


# ==========================================
# 2B. 🌟 NEW: STOCK BATCH & EXPIRY SCHEMAS
# ==========================================
class StockBatchResponse(BaseModel):
    id: int
    product_id: int
    quantity_received: Decimal
    quantity_remaining: Decimal
    unit_cost: Decimal
    expiry_date: Optional[datetime.date] = None
    received_date: datetime.datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class ExpiringBatchAlert(BaseModel):
    batch_id: int
    product_id: int
    product_name: str
    quantity_remaining: Decimal
    expiry_date: datetime.date
    days_until_expiry: int

    class Config:
        from_attributes = True


# ==========================================
# 3. CUSTOMER PROFILE & KHATA SCHEMAS
# ==========================================
class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Customer name cannot be empty")
    phone: Optional[str] = Field(default=None, description="Optional phone number format")
    # 🌟 NEW: optional at creation — existing frontend calls that omit these still work
    credit_limit: Optional[Decimal] = Field(default=None, ge=0, description="Max Udhaar allowed. Omit for no limit.")
    credit_block_mode: Optional[str] = Field(
        default="WARN", description="'WARN' to allow overage with a warning, 'BLOCK' to hard-stop at the limit."
    )

    @model_validator(mode="after")
    def validate_block_mode(self) -> "CustomerCreate":
        if self.credit_block_mode not in ("WARN", "BLOCK"):
            raise ValueError("credit_block_mode must be either 'WARN' or 'BLOCK'.")
        return self

class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    phone: Optional[str] = None
    credit_limit: Optional[Decimal] = Field(default=None, ge=0)
    credit_block_mode: Optional[str] = None

class CustomerResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    total_credit_due: Decimal
    # 🌟 NEW fields — additive, existing frontend code reading this object is unaffected
    credit_limit: Optional[Decimal] = None
    credit_block_mode: str = "WARN"

    class Config:
        from_attributes = True

class RepaymentRequest(BaseModel):
    amount_paid: Decimal = Field(..., gt=0, description="Repayment amount must be greater than zero")
    payment_method: str = Field(..., description="CASH or ONLINE")
    notes: Optional[str] = Field(default=None)


# ==========================================
# 4. CART & BILLING TRANSACTION SCHEMAS
# ==========================================
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(..., gt=0, description="Quantity must be greater than zero")

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    amount_paid: Decimal = Field(default=Decimal("0.00"), ge=0)
    payment_method: str  # CASH, ONLINE, PARTIAL, CREDIT
    payment_status: Optional[str] = "PAID"
    customer_info: Optional[str] = None
    customer_id: Optional[int] = Field(default=None, description="Required for credit or partial sales")

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    brand: Optional[str] = "Local"
    unit_type: Optional[str] = "PIECE"
    quantity: Decimal
    unit_price: Decimal

    @model_validator(mode="before")
    @classmethod
    def resolve_product_relationship(cls, data):
        if hasattr(data, "product") and data.product:
            setattr(data, "product_name", data.product.name)
            setattr(data, "brand", data.product.brand)
            setattr(data, "unit_type", data.product.unit_type)
        return data

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    total_amount: Decimal
    amount_paid: Decimal
    amount_pending: Decimal
    payment_method: str
    payment_status: str
    customer_id: Optional[int]
    customer_info: Optional[str]
    timestamp: datetime.datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


# ==========================================
# 5. AUDIT REPORT AND LEDGER SCHEMAS
# ==========================================
class StockTransactionResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity_changed: Decimal
    type: str
    unit_cost: Decimal
    total_cost: Decimal
    notes: Optional[str] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

class LowStockAlert(BaseModel):
    product_id: int
    product_name: str
    current_quantity: Decimal
    brand: str

    class Config:
        from_attributes = True

class DashboardAnalytics(BaseModel):
    total_sales_revenue: Decimal
    total_liquid_received: Decimal
    total_market_debt: Decimal
    total_purchase_spend: Decimal
    overall_net_profit: Decimal
    top_selling_product: Optional[ProductSearchResponse] = None
    low_stock_count: int
    low_stock_alerts: List[LowStockAlert]


# ==========================================
# 6. FINANCE & EXPENSE SCHEMA FIXES
# ==========================================
class ExpenseCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Out-of-pocket amount spent on the expense")
    category: str = Field(..., min_length=1, max_length=50, description="Type of expense, e.g., RENT, UTILITIES, WAGES, MISC")
    notes: Optional[str] = Field(None, max_length=255, description="Any payment details, invoice numbers, or descriptions")

class ExpenseResponse(BaseModel):
    id: int
    type: str
    amount: Decimal
    category: str
    is_automated: bool
    notes: Optional[str] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True
