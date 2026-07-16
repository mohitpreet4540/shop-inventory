from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from decimal import Decimal
import datetime

# ==========================================
# 1. CATEGORY MANAGEMENT SCHEMAS
# ==========================================

# Used when creating a new category or subcategory
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the category")
    parent_id: Optional[int] = Field(None, description="ID of parent category if this is a subcategory")

# Used when updating an existing category
class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    parent_id: Optional[int] = None

# Simple output structure for basic category lists
class CategorySimpleResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

# Standard output structure for category profiles
class CategoryResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True

# Hierarchical output structure used for the category tree view
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

# Used when creating a new product in inventory
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

    # Verification rule to prevent pricing logic errors
    @model_validator(mode="after")
    def verify_pricing_margins(self) -> "ProductCreate":
        if self.selling_price < self.cost_price:
            raise ValueError("Operational Mismatch: Selling price cannot be lower than wholesale cost price.")
        return self

# Standard output structure for a product profile
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

# Light structure used when searching or filtering products quickly
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

# Used when updating product prices
class ProductPriceUpdate(BaseModel):
    selling_price: Decimal = Field(..., gt=0)
    cost_price: Optional[Decimal] = Field(None, gt=0)


# ==========================================
# 3. CUSTOMER PROFILE & KHATA SCHEMAS
# ==========================================

# Used when creating a new customer ledger profile
class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Customer name cannot be empty")
    phone: Optional[str] = Field(default=None, description="Optional phone number format")

# Standard output structure for customer profiles and running balances
class CustomerResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    total_credit_due: Decimal
    
    class Config:
        from_attributes = True

# Used when processing a manual credit (Udhaar) repayment
class RepaymentRequest(BaseModel):
    amount_paid: Decimal = Field(..., gt=0, description="Repayment amount must be greater than zero")
    payment_method: str = Field(..., description="CASH or ONLINE")
    notes: Optional[str] = Field(default=None)


# ==========================================
# 4. CART & BILLING TRANSACTION SCHEMAS
# ==========================================

# Line items used when creating an order
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(..., gt=0, description="Quantity must be greater than zero")

# Main order creation request
class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    amount_paid: Decimal = Field(default=Decimal("0.00"), ge=0)
    payment_method: str  # CASH, ONLINE, PARTIAL, CREDIT
    customer_id: Optional[int] = Field(default=None, description="Required for credit or partial sales")

# Line items inside an order response details view
from pydantic import BaseModel, Field, model_validator # Ensure model_validator is imported

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
        # If this is a lazy-loaded SQLAlchemy object model
        if hasattr(data, "product") and data.product:
            setattr(data, "product_name", data.product.name)
            setattr(data, "brand", data.product.brand)
            setattr(data, "unit_type", data.product.unit_type)
        return data

    class Config:
        from_attributes = True

# Main order response record data
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

# Output structure for stock logging and auditing tools
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

# Output structure for low stock visual alert cards
class LowStockAlert(BaseModel):
    product_id: int
    product_name: str
    current_quantity: Decimal
    brand: str

    class Config:
        from_attributes = True

# Output structure for the main analytics summary panel
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
# 6. EXTERNAL LOOKUP SERVICES
# ==========================================

# Output structure for public internet barcode lookups
class BarcodeLookupResponse(BaseModel):
    found: bool = Field(..., description="Flags if item exists in global registry")
    name: Optional[str] = None
    brand: Optional[str] = "Local"
    image_url: Optional[str] = None
    message: str

# Insert this into app/schemas.py

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    brand: Optional[str] = None
    barcode: Optional[str] = None
    unit_type: Optional[str] = None
    cost_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    current_quantity: Optional[Decimal] = None
    image_url: Optional[str] = None
    expiry_date: Optional[datetime.date] = None  # 🌟 Allows retroactive assignment of expiry dates
    category_ids: Optional[List[int]] = None      # Allows updating product categories dynamically

    class Config:
        from_attributes = True


# ==========================================
# PRODUCT RESTOCK VALIDATION SCHEMA
# ==========================================
class ProductRestock(BaseModel):
    quantity: Decimal = Field(..., gt=0, description="Incoming wholesale stock quantity")
    unit_cost: Decimal = Field(..., ge=0, description="Actual supplier cost price per individual unit")
    notes: Optional[str] = Field(None, max_length=255, description="Optional invoice numbers or delivery notes")

    class Config:
        from_attributes = True