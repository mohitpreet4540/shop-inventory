import sys
from decimal import Decimal
import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models

def seed_database():
    print("Starting automated database seeding...")
    db: Session = SessionLocal()
    
    try:
        
        print("🧹 Cleaning up old database records...")
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

       
        print(" Injecting sample inventory products...")
        p1 = models.Product(
            name="Logitech Wireless Mouse", cost_price=Decimal("800.00"), 
            selling_price=Decimal("1200.00"), current_quantity=50, category_id=electronics.id
        )
        p2 = models.Product(
            name="Mechanical Keyboard", cost_price=Decimal("2500.00"), 
            selling_price=Decimal("3500.00"), current_quantity=12, category_id=electronics.id
        )
        p3 = models.Product(
            name="Maggi Noodles Packet", cost_price=Decimal("10.00"), 
            selling_price=Decimal("14.00"), current_quantity=200, category_id=groceries.id
        )
        #  Low Stock Item to test your dashboard alerts instantly!
        p4 = models.Product(
            name="USB-C Charging Cable", cost_price=Decimal("150.00"), 
            selling_price=Decimal("300.00"), current_quantity=2, category_id=electronics.id
        )
        p5 = models.Product(
            name="Aloe Vera Face Wash", cost_price=Decimal("120.00"), 
            selling_price=Decimal("180.00"), current_quantity=25, category_id=cosmetics.id
        )

        db.add_all([p1, p2, p3, p4, p5])
        db.flush()

        
        print("📜 Generating initial stock transaction history audit logs...")
        for prod in [p1, p2, p3, p4, p5]:
            log = models.StockTransaction(
                product_id=prod.id, quantity_changed=prod.current_quantity,
                type="INITIAL_STOCK", notes="Automated system setup seeding"
            )
            db.add(log)

       
        print("🛒 Simulating checkout order logs...")
        
        order1 = models.Order(
            total_amount=Decimal("2700.00"), payment_method="ONLINE", payment_status="PAID",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(order1)
        db.flush()
        
        oi1 = models.OrderItem(order_id=order1.id, product_id=p1.id, quantity=2, unit_price=Decimal("2400.00"))
        oi2 = models.OrderItem(order_id=order1.id, product_id=p4.id, quantity=1, unit_price=Decimal("300.00"))
        db.add_all([oi1, oi2])
        
        # Deduct items from stock to match realities
        p1.current_quantity -= 2
        p4.current_quantity -= 1
        
        # Log the sale transactions
        db.add(models.StockTransaction(product_id=p1.id, quantity_changed=-2, type="SALE", notes=f"Order #{order1.id}"))
        db.add(models.StockTransaction(product_id=p4.id, quantity_changed=-1, type="SALE", notes=f"Order #{order1.id}"))

        # Order 2: Massive order for Maggi (Testing top seller aggregation)
        order2 = models.Order(
            total_amount=Decimal("700.00"), payment_method="CASH", payment_status="PAID",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(order2)
        db.flush()
        
        oi3 = models.OrderItem(order_id=order2.id, product_id=p3.id, quantity=50, unit_price=Decimal("700.00"))
        db.add(oi3)
        p3.current_quantity -= 50
        db.add(models.StockTransaction(product_id=p3.id, quantity_changed=-50, type="SALE", notes=f"Order #{order2.id}"))

        db.commit()
        print("🎉 Database successfully seeded with rich mock data!")
        
    except Exception as e:
        db.rollback()
        print(f" Error during seeding lifecycle: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()