from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import Optional
from app.database import get_db
from app.models import OrderItem, Product
from app.schemas import DashboardAnalyticsSchema

router = APIRouter(prefix="/dashboard", tags=["Dashboard Analytics"])

@router.get("/", response_model=DashboardAnalyticsSchema)
def get_dashboard_analytics(db: Session = Depends(get_db)):
    try:
        #  1. CALCULATE FINANCIAL METRICS
        all_sold_items = db.query(OrderItem).all()
        
        total_sales_revenue = Decimal("0.00")
        total_purchase_spend = Decimal("0.00")
        
        for item in all_sold_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                total_sales_revenue += item.unit_price
                item_cost = Decimal(item.quantity) * product.cost_price
                total_purchase_spend += item_cost
        
        overall_net_profit = total_sales_revenue - total_purchase_spend
        
        top_product_query = (
            db.query(OrderItem.product_id, func.sum(OrderItem.quantity).label("total_sold"))
            .group_by(OrderItem.product_id)
            .order_by(func.sum(OrderItem.quantity).desc())
            .first()
        )
        
        top_selling_product = None
        if top_product_query:
            prod_id, total_qty = top_product_query
            product_details = db.query(Product).filter(Product.id == prod_id).first()
            if product_details:
                top_selling_product = {
                    "id": product_details.id,
                    "name": product_details.name,
                    "total_quantity_sold": total_qty
                }

        low_stock_products = db.query(Product).filter(Product.current_quantity <= 5).all()
        
        # 🌟 4. RETURN EVERYTHING SECURELY
        return {
            "total_sales_revenue": total_sales_revenue,
            "total_purchase_spend": total_purchase_spend,
            "overall_net_profit": overall_net_profit,
            "top_selling_product": top_selling_product, # Returns the top product or None if no sales yet
            "low_stock_count": len(low_stock_products),
            "low_stock_alerts": low_stock_products
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load analytics: {str(e)}")