from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from app.database import get_db
from app.models import OrderItem, Product
from app.schemas import DashboardAnalyticsSchema

router = APIRouter(prefix="/dashboard", tags=["Dashboard Analytics"])

@router.get("/", response_model=DashboardAnalyticsSchema)
def get_dashboard_analytics(db: Session = Depends(get_db)):
    try:
        #  1. CALCULATE FINANCIAL METRICS
        # Fetch all sold order line items along with their parent product details
        all_sold_items = db.query(OrderItem).all()
        
        total_sales_revenue = Decimal("0.00")
        total_purchase_spend = Decimal("0.00")
        
        for item in all_sold_items:
            # Look up the product details to get the cost price
            product = db.query(Product).filter(Product.id == item.product_id).first()
            
            if product:
                # Revenue = quantity sold * price sold at
                total_sales_revenue += item.unit_price  # individual line totals are already saved here
                
                # Purchase Spend = quantity sold * what the shopkeeper paid for it
                item_cost = Decimal(item.quantity) * product.cost_price
                total_purchase_spend += item_cost
        
        # Net Profit = Total Revenue - Total Cost Spend
        overall_net_profit = total_sales_revenue - total_purchase_spend
        
        # 2. GENERATE LOW STOCK ALERTS
        # Automatically grab any products where quantity has fallen to 5 or less
        low_stock_products = db.query(Product).filter(Product.current_quantity <= 5).all()
        
        #  3. PACK EVERYTHING INTO THE RESPONSE CONTRACT
        return {
            "total_sales_revenue": total_sales_revenue,
            "total_purchase_spend": total_purchase_spend,
            "overall_net_profit": overall_net_profit,
            "low_stock_count": len(low_stock_products),
            "low_stock_alerts": low_stock_products
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load analytics: {str(e)}")