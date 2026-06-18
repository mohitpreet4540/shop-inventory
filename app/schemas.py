from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from decimal import Decimal
import datetime

# --- CATEGORY SCHEMAS ---
class CategoryCreateSchema(BaseModel):
    name: str
    parent_id: Optional[int] = None

class CategoryResponseSchema(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# --- PRODUCT SCHEMAS ---
class ProductCreateSchema(BaseModel):
    name: str
    brand: Optional[str] = "Local"            
    barcode: Optional[str] = None             
    unit_type: Optional[str] = "PIECE"        
    cost_price: Decimal     
    selling_price: Decimal  
    current_quantity: Decimal = Decimal("0.0") 
    category_id: int

class ProductResponseSchema(BaseModel):
    id: int
    name: str
    brand: str                                
    barcode: Optional[str] = None             
    unit_type: str                            
    cost_price: Decimal     
    selling_price: Decimal  
    current_quantity: Decimal                 
    category_id: int
    
    class Config:
        from_attributes = True


# --- CHECKOUT / CART SCHEMAS ---
class CartItemSchema(BaseModel):
    product_id: Optional[int] = None       
    barcode: Optional[str] = None          
    quantity: Decimal = Field(..., gt=0)      

class OrderCreateSchema(BaseModel):
    payment_method: str  # "CASH", "ONLINE", "PARTIAL", or "CREDIT"
    items: List[CartItemSchema]
    
    # 💰 🌟 NEW: Structured Financial Split Layer
    total_amount: Decimal = Field(..., ge=0, description="The complete value of the bill invoice")
    amount_paid: Decimal = Field(..., ge=0, description="Actual physical or digital cash received upfront")
    amount_pending: Decimal = Field(..., ge=0, description="The outstanding debt ledger balance (Udhaar)")
    customer_info: Optional[str] = Field(default="Walk-in Customer", description="Format tracking line: 'Name (Phone)'")

    # 🛡️ 🌟 NEW: Strict Mathematical Data Guard Validator
    @model_validator(mode='after')
    def validate_ledger_math(self) -> 'OrderCreateSchema':
        # 1. Check if the math balances down correctly
        if self.amount_paid + self.amount_pending != self.total_amount:
            raise ValueError(
                f"Ledger Math Failure: Amount Paid (₹{self.amount_paid}) + Amount Pending (₹{self.amount_pending}) "
                f"must equal Total Amount (₹{self.total_amount})."
            )
        
        # 2. Check if Udhaar is registered anonymously
        if self.amount_pending > 0 and (not self.customer_info or self.customer_info == "Walk-in Customer"):
            raise ValueError(
                "Security Mandate: Cannot process outstanding balance (Udhaar) under an anonymous 'Walk-in Customer' profile."
            )
            
        return self


# 🌟 NEW: Updated to match individual row outputs with ledger split models
class OrderItemResponseSchema(BaseModel):
    product_id: int
    product_name: str                      
    brand: str                             
    unit_type: str                         
    quantity: Decimal
    unit_price: Decimal

    class Config:
        from_attributes = True


class OrderResponseSchema(BaseModel):
    id: int
    total_amount: Decimal  
    amount_paid: Decimal     # 🌟 Added to match updated database layout
    amount_pending: Decimal  # 🌟 Added to track specific invoice debts
    payment_method: str
    payment_status: str
    customer_info: Optional[str] = "Walk-in Customer"
    timestamp: datetime.datetime
    items: List[OrderItemResponseSchema]   
    
    class Config:
        from_attributes = True


# --- INVENTORY REFILL SCHEMA ---
class StockIncrementRequest(BaseModel):
    product_id: int
    quantity: Decimal = Field(..., gt=0, description="Must be greater than zero") 
    notes: str = Field(default="Manual restock", description="Wholesale delivery stock replenishment")
    cost_price: Optional[Decimal] = Field(None, gt=0)
    selling_price: Optional[Decimal] = Field(None, gt=0)
    
class LowStockProductSchema(BaseModel):
    id: int
    name: str
    current_quantity: Decimal                 

    class Config:
        from_attributes = True

class TopSellingProductSchema(BaseModel):
    id: int
    name: str
    total_quantity_sold: Decimal              

    class Config:
        from_attributes = True        


# --- UPDATED EXECUTIVE DASHBOARD METRICS ---
class DashboardAnalyticsSchema(BaseModel):
    total_sales_revenue: Decimal   # Total booked invoices turnover value
    total_liquid_received: Decimal # 🌟 NEW: Total hard liquid cash collected in hand
    total_market_debt: Decimal     # 🌟 NEW: Total outstanding credit value hanging outside (Udhaar)
    total_purchase_spend: Decimal
    overall_net_profit: Decimal
    top_selling_product: Optional[TopSellingProductSchema] = None
    low_stock_count: int
    low_stock_alerts: List[LowStockProductSchema]


class StockTransactionResponseSchema(BaseModel):
    id: int
    product_id: int
    product_name: str 
    quantity_changed: Decimal                 
    type: str       
    notes: Optional[str] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True
        
# --- SEARCH RESPONSE SCHEMA ---
class ProductSearchResponseSchema(BaseModel):
    id: int
    name: str
    brand: str
    barcode: Optional[str] = None
    unit_type: str
    selling_price: Decimal
    current_quantity: Decimal

    class Config:
        from_attributes = True

        # --- PRODUCT PRICE UPDATE SCHEMA ---
class ProductPriceUpdateSchema(BaseModel):
    selling_price: Decimal = Field(..., gt=0, description="The new retail selling price must be greater than zero")
    cost_price: Optional[Decimal] = Field(None, gt=0, description="Optional updated wholesale cost price")