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
    cost_price: Decimal     # Changed from float to Decimal for currency safety
    selling_price: Decimal  # Changed from float to Decimal for currency safety
    current_quantity: int = 0
    category_id: int

class ProductResponseSchema(BaseModel):
    id: int
    name: str
    cost_price: Decimal     # Changed from float to Decimal
    selling_price: Decimal  # Changed from float to Decimal
    current_quantity: int
    category_id: int
    
    class Config:
        from_attributes = True


# --- CHECKOUT / CART SCHEMAS ---
class CartItemSchema(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderCreateSchema(BaseModel):
    payment_method: str  # "CASH" or "ONLINE"
    items: List[CartItemSchema]

class OrderResponseSchema(BaseModel):
    id: int
    total_amount: Decimal  # Changed from float to Decimal to match DB execution
    payment_method: str
    payment_status: str
    timestamp: datetime.datetime
    
    class Config:
        from_attributes = True


# --- INVENTORY REFILL SCHEMA ---
class StockIncrementRequest(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, description="Must be greater than zero")
    notes: str = Field(default="Manual restock", description="Changed from 'note' to 'notes' to match DB column")

