from pydantic import BaseModel, Field
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
    # 🌟 UPDATED: Both are optional now, but the router validates that at least one is present
    product_id: Optional[int] = None       
    barcode: Optional[str] = None          # 🌟 Added so the barcode scanner can pass raw data strings
    quantity: Decimal = Field(..., gt=0)      

class OrderCreateSchema(BaseModel):
    payment_method: str  # "CASH" or "ONLINE"
    items: List[CartItemSchema]


# 🌟 NEW: Added to represent individual row outputs on a billing invoice receipt
class OrderItemResponseSchema(BaseModel):
    product_id: int
    product_name: str                      
    brand: str                             
    unit_type: str                         # Outputs "KG", "METER", or "PIECE"
    quantity: Decimal
    unit_price: Decimal

    class Config:
        from_attributes = True


class OrderResponseSchema(BaseModel):
    id: int
    total_amount: Decimal  
    payment_method: str
    payment_status: str
    timestamp: datetime.datetime
    items: List[OrderItemResponseSchema]   # 🌟 Injected nested structure to display exactly what items were sold
    
    class Config:
        from_attributes = True


# --- INVENTORY REFILL SCHEMA ---
class StockIncrementRequest(BaseModel):
    product_id: int
    quantity: Decimal = Field(..., gt=0, description="Must be greater than zero") 
    notes: str = Field(default="Manual restock", description="Wholesale delivery stock replenishment")
    # 🌟 NEW: Optional price updates
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

class DashboardAnalyticsSchema(BaseModel):
    total_sales_revenue: Decimal
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