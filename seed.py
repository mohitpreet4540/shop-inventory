import sys
from decimal import Decimal
import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models

def seed_database():
    print("Starting automated database seeding with Brand & Metric configurations...")
    db: Session = SessionLocal()
    
    try:
        print("🧹 Cleaning up old database records...")
        db.query(models.FinanceLedger).delete() # Added clean-up for the cash ledger too
        db.query(models.StockTransaction).delete()
        db.query(models.OrderItem).delete()
        db.query(models.Order).delete()
        db.query(models.Product).delete()
        db.query(models.Category).delete()
        db.commit()

        print("📁 Injecting base categories...")
        electronics = models.Category(name="Electronics")
        groceries = models.Category(name="Groceries")
        cosmetics = models.Category(name="Cosmetics")
        
        db.add_all([electronics, groceries, cosmetics])
        db.flush() 

        print("📦 Injecting sample inventory products with Brands and custom Unit Types...")
        p1 = models.Product(
            name="Wireless Mouse", brand="Logitech", barcode="8901058860710",
            cost_price=Decimal("800.00"), selling_price=Decimal("1200.00"), 
            current_quantity=Decimal("50.00"), unit_type="PIECE", category_id=electronics.id
        )
        p2 = models.Product(
            name="Mechanical Keyboard", brand="Cosmic Byte", barcode="8901725111222",
            cost_price=Decimal("2500.00"), selling_price=Decimal("3500.00"), 
            current_quantity=Decimal("12.00"), unit_type="PIECE", category_id=electronics.id
        )
        p3 = models.Product(
            name="Maggi Noodles Packet", brand="Nestle Maggi", barcode="8901058860123",
            cost_price=Decimal("10.00"), selling_price=Decimal("14.00"), 
            current_quantity=Decimal("200.00"), unit_type="PIECE", category_id=groceries.id
        )
        # 🌟 Loose Metric Item 1: Test decimal deduction with Kilograms (Sugar)
        p4 = models.Product(
            name="Loose White Sugar", brand="Local", barcode="LOCAL_SUGAR_03",
            cost_price=Decimal("36.00"), selling_price=Decimal("44.00"), 
            current_quantity=Decimal("150.50"), unit_type="KG", category_id=groceries.id
        )
        # 🌟 Metric Item 2: Test Low Stock warning (Under 3 Meters)
        p5 = models.Product(
            name="Electrical Wire Black", brand="Havells", barcode="LOCAL_WIRE_04",
            cost_price=Decimal("15.00"), selling_price=Decimal("25.00"), 
            current_quantity=Decimal("2.50"), unit_type="METER", category_id=electronics.id
        )
        # Cosmetic Item to complete the circle
        p6 = models.Product(
            name="Aloe Vera Face Wash", brand="Patanjali", barcode="8904109450321",
            cost_price=Decimal("120.00"), selling_price=Decimal("180.00"), 
            current_quantity=Decimal("25.00"), unit_type="PIECE", category_id=cosmetics.id
        )

        db.add_all([p1, p2, p3, p4, p5, p6])
        db.flush()

        print("📜 Generating initial stock transaction history audit logs...")
        for prod in [p1, p2, p3, p4, p5, p6]:
            log = models.StockTransaction(
                product_id=prod.id, quantity_changed=prod.current_quantity,
                type="INITIAL_STOCK", notes="Automated system setup seeding"
            )
            db.add(log)

        print("🛒 Simulating checkout order logs...")
        
        # Order 1: Mixed purchase (Logitech Mouse + USB/Meters tracking)
        # 2 Mice (2 * 1200 = 2400) + 1.5 meters/units of Havells Wire (1.5 * 25 = 37.50) = 2437.50
        order1 = models.Order(
            total_amount=Decimal("2437.50"), payment_method="ONLINE", payment_status="PAID",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(order1)
        db.flush()
        
        # 🌟 FIXED: unit_price holds the dynamic unit rate, not the aggregated checkout total!
        oi1 = models.OrderItem(order_id=order1.id, product_id=p1.id, quantity=Decimal("2.00"), unit_price=Decimal("1200.00"))
        oi2 = models.OrderItem(order_id=order1.id, product_id=p5.id, quantity=Decimal("1.50"), unit_price=Decimal("25.00"))
        db.add_all([oi1, oi2])
        
        # Deduct items from stock using precise decimal arithmetic
        p1.current_quantity -= Decimal("2.00")
        p5.current_quantity -= Decimal("1.50")
        
        # Log the sale transactions using standard negative decimal values
        db.add(models.StockTransaction(product_id=p1.id, quantity_changed=Decimal("-2.00"), type="SALE", notes=f"Order #{order1.id}"))
        db.add(models.StockTransaction(product_id=p5.id, quantity_changed=Decimal("-1.50"), type="SALE", notes=f"Order #{order1.id}"))

        # Order 2: Massive order for Maggi (Testing top seller aggregation)
        # 50 Packets of Maggi * 14 = 700.00
        order2 = models.Order(
            total_amount=Decimal("700.00"), payment_method="CASH", payment_status="PAID",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(order2)
        db.flush()
        
        oi3 = models.OrderItem(order_id=order2.id, product_id=p3.id, quantity=Decimal("50.00"), unit_price=Decimal("14.00"))
        db.add(oi3)
        p3.current_quantity -= Decimal("50.00")
        db.add(models.StockTransaction(product_id=p3.id, quantity_changed=Decimal("-50.00"), type="SALE", notes=f"Order #{order2.id}"))

        db.commit()
        print("🎉 Database successfully seeded with rich, unit-aware mock retail data!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding lifecycle: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()