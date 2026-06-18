from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models import Order, Product, FinanceLedger, OrderItem
from app.schemas import DashboardAnalyticsSchema, LowStockProductSchema, TopSellingProductSchema

# Clean, isolated router namespace configuration
router = APIRouter(prefix="/dashboard", tags=["Executive Dashboard"])

@router.get("/metrics", response_model=DashboardAnalyticsSchema)
def get_dashboard_analytics(
    range_type: str = Query("today", description="Filter time windows: 'today', 'weekly', or 'monthly'"),
    db: Session = Depends(get_db)
):
    now_utc = datetime.now(timezone.utc)
    
    # 1. Establish the target time horizon filter matching your selection criteria
    if range_type == "weekly":
        start_time = now_utc - timedelta(days=7)
    elif range_type == "monthly":
        start_time = now_utc - timedelta(days=30)
    else:  # Default fallback path: "today"
        start_time = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        # 2. Extract operational records corresponding to the specific date interval boundary
        orders = db.query(Order).filter(Order.timestamp >= start_time).all()
        
        # 3. Process the split-ledger financial cash-flow matrices
        total_sales_revenue = Decimal("0.00")
        total_liquid_received = Decimal("0.00")
        total_market_debt = Decimal("0.00")
        
        for order in orders:
            total_sales_revenue += order.total_amount
            total_liquid_received += order.amount_paid
            total_market_debt += order.amount_pending

        # 4. Compute wholesale stock purchase expenditure via automation ledger logs
        purchase_spend_query = db.query(func.sum(FinanceLedger.amount))\
            .filter(FinanceLedger.type == "PURCHASE", FinanceLedger.timestamp >= start_time)\
            .scalar()
        total_purchase_spend = Decimal(str(purchase_spend_query)) if purchase_spend_query else Decimal("0.00")

        # 5. Compute net operating profitability thresholds
        overall_net_profit = total_sales_revenue - total_purchase_spend

        # 6. Extract the top-moving product profile over the selected timeline
        top_product_data = db.query(
            OrderItem.product_id,
            func.sum(OrderItem.quantity).label("total_sold")
        ).join(Order).filter(Order.timestamp >= start_time)\
         .group_by(OrderItem.product_id)\
         .order_by(func.sum(OrderItem.quantity).desc())\
         .first()

        top_selling_product = None
        if top_product_data:
            prod_record = db.query(Product).filter(Product.id == top_product_data.product_id).first()
            if prod_record:
                top_selling_product = TopSellingProductSchema(
                    id=prod_record.id,
                    name=prod_record.name,
                    total_quantity_sold=Decimal(str(top_product_data.total_sold))
                )

        # 7. Identify critical stock depletion thresholds (Low Stock Alerts)
        LOW_STOCK_THRESHOLD = Decimal("10.00")
        low_stock_products = db.query(Product).filter(Product.current_quantity <= LOW_STOCK_THRESHOLD).all()
        
        low_stock_alerts = [
            LowStockProductSchema(id=p.id, name=p.name, current_quantity=p.current_quantity)
            for p in low_stock_products
        ]
        low_stock_count = len(low_stock_alerts)

        # 8. Assemble structured analytical payload return structure
        return DashboardAnalyticsSchema(
            total_sales_revenue=total_sales_revenue,
            total_liquid_received=total_liquid_received,
            total_market_debt=total_market_debt,
            total_purchase_spend=total_purchase_spend,
            overall_net_profit=overall_net_profit,
            top_selling_product=top_selling_product,
            low_stock_count=low_stock_count,
            low_stock_alerts=low_stock_alerts
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to compile dashboard metrics aggregation engine data: {str(e)}"
        )