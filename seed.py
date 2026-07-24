import sys
from decimal import Decimal
import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.dependencies import hash_password  # 🌟 NEW: for seeding default login accounts

def seed_database():
    print("🚀 Starting Production-Grade Store Database Seeding...")
    db: Session = SessionLocal()

    try:
        print("🧹 Flushing old database records to reset integrity chains...")
        db.query(models.FinanceLedger).delete()
        db.query(models.StockTransaction).delete()
        db.query(models.OrderItem).delete()
        db.query(models.Order).delete()
        db.query(models.Product).delete()
        db.query(models.Category).delete()
        db.query(models.Customer).delete()  # 🌟 NEW: also reset customers on reseed
        db.query(models.User).delete()  # 🌟 NEW: also reset demo login accounts on reseed
        db.commit()

        # =================================================================
        # 🌟 NEW: DEMO LOGIN ACCOUNTS (one per role — DEV ONLY, change passwords in real use)
        # =================================================================
        print("🔐 Injecting demo login accounts (owner / admin / cashier)...")
        db.add_all([
            models.User(username="owner", hashed_password=hash_password("owner123"), role="OWNER", is_active=True),
            models.User(username="admin", hashed_password=hash_password("admin123"), role="ADMIN", is_active=True),
            models.User(username="cashier", hashed_password=hash_password("cashier123"), role="CASHIER", is_active=True),
        ])
        db.commit()
        print("   -> owner / owner123   (full access)")
        print("   -> admin / admin123   (manage inventory, finance, reports)")
        print("   -> cashier / cashier123 (billing counter only)")

        print("📁 Injecting Department Categories...")
        groceries = models.Category(name="Groceries & Staples")
        electronics = models.Category(name="Electronics & Electricals")
        cosmetics = models.Category(name="Cosmetics & Personal Care")
        beverages = models.Category(name="Beverages & Snacks")

        db.add_all([groceries, electronics, cosmetics, beverages])
        db.flush()

        print("📦 Injecting 15 Genuine Product SKU Records (Many-to-Many Mapped)...")

        # --- GROCERIES & STAPLES ---
        p1 = models.Product(
            name="Maggi 2-Minute Instant Noodles", brand="Nestlé Maggi", barcode="8901058002479",
            cost_price=Decimal("11.50"), selling_price=Decimal("14.00"),
            current_quantity=Decimal("350.00"), unit_type="PIECE", categories=[groceries],
            image_url="/static/uploads/8901058002479.jpg"
        )
        p2 = models.Product(
            name="Tata Salt Iodized", brand="Tata", barcode="8901058860123",
            cost_price=Decimal("22.00"), selling_price=Decimal("28.00"),
            current_quantity=Decimal("120.00"), unit_type="PIECE", categories=[groceries],
            image_url="/static/uploads/8901058860123.jpg"
        )
        p3 = models.Product(
            name="Fortune Premium Kachi Ghani Mustard Oil", brand="Fortune", barcode="8906007282361",
            cost_price=Decimal("145.00"), selling_price=Decimal("175.00"),
            current_quantity=Decimal("60.00"), unit_type="PIECE", categories=[groceries],
            image_url="/static/uploads/8906007282361.jpg"
        )
        p4 = models.Product(
            name="Loose Pure White Sugar", brand="Local Wholesale", barcode="LOCAL_SUGAR_KG_01",
            cost_price=Decimal("37.00"), selling_price=Decimal("45.00"),
            current_quantity=Decimal("240.50"), unit_type="KG", categories=[groceries],
            image_url=None
        )

        # --- ELECTRONICS & ELECTRICALS ---
        p5 = models.Product(
            name="Logitech B100 Optical USB Mouse", brand="Logitech", barcode="8901058860710",
            cost_price=Decimal("290.00"), selling_price=Decimal("399.00"),
            current_quantity=Decimal("45.00"), unit_type="PIECE", categories=[electronics],
            image_url="/static/uploads/8901058860710.jpg"
        )
        p6 = models.Product(
            name="Cosmic Byte CB-GK-16 Mechanical Keyboard", brand="Cosmic Byte", barcode="8901725111222",
            cost_price=Decimal("1950.00"), selling_price=Decimal("2499.00"),
            current_quantity=Decimal("15.00"), unit_type="PIECE", categories=[electronics],
            image_url="/static/uploads/8901725111222.jpg"
        )
        p7 = models.Product(
            name="Havells 3-Core Heavy Duty Electrical Wire", brand="Havells", barcode="LOCAL_WIRE_MTR_02",
            cost_price=Decimal("18.00"), selling_price=Decimal("30.00"),
            current_quantity=Decimal("180.00"), unit_type="METER", categories=[electronics],
            image_url=None
        )

        # --- COSMETICS & PERSONAL CARE ---
        p8 = models.Product(
            name="Patanjali Aloe Vera Face Wash", brand="Patanjali", barcode="8904109450321",
            cost_price=Decimal("75.00"), selling_price=Decimal("95.00"),
            current_quantity=Decimal("80.00"), unit_type="PIECE", categories=[cosmetics],
            image_url="/static/uploads/8904109450321.jpg"
        )
        p9 = models.Product(
            name="Dettol Liquid Antiseptic", brand="Dettol", barcode="8901396326121",
            cost_price=Decimal("270.00"), selling_price=Decimal("331.00"),
            current_quantity=Decimal("35.00"), unit_type="PIECE", categories=[cosmetics],
            image_url="/static/uploads/8901396326121.jpg"
        )
        p10 = models.Product(
            name="Colgate MaxFresh Spicy Fresh Gel", brand="Colgate", barcode="8901138836017",
            cost_price=Decimal("82.00"), selling_price=Decimal("110.00"),
            current_quantity=Decimal("90.00"), unit_type="PIECE", categories=[cosmetics],
            image_url="/static/uploads/8901138836017.jpg"
        )

        # --- BEVERAGES & SNACKS ---
        p11 = models.Product(
            name="Maggi Arôme Liquid Seasoning 250g", brand="Nestlé", barcode="3033710084913",
            cost_price=Decimal("180.00"), selling_price=Decimal("240.00"),
            current_quantity=Decimal("28.00"), unit_type="PIECE", categories=[beverages],
            image_url="/static/uploads/3033710084913.jpg"
        )
        p12 = models.Product(
            name="Coca-Cola Original Taste 500ml", brand="Coca-Cola", barcode="5449000000996",
            cost_price=Decimal("32.00"), selling_price=Decimal("40.00"),
            current_quantity=Decimal("200.00"), unit_type="PIECE", categories=[beverages],
            image_url="/static/uploads/5449000000996.jpg"
        )
        p13 = models.Product(
            name="Cadbury Dairy Milk Silk Chocolate", brand="Cadbury", barcode="7622210811241",
            cost_price=Decimal("68.00"), selling_price=Decimal("80.00"),
            current_quantity=Decimal("110.00"), unit_type="PIECE", categories=[beverages],
            image_url="/static/uploads/7622210811241.jpg"
        )
        p14 = models.Product(
            name="Lays Potato Chips India's Magic Masala", brand="Lays", barcode="8901491101838",
            cost_price=Decimal("16.00"), selling_price=Decimal("20.00"),
            current_quantity=Decimal("150.00"), unit_type="PIECE", categories=[beverages],
            image_url="/static/uploads/8901491101838.jpg"
        )
        p15 = models.Product(
            name="Amul Butter 100g", brand="Amul", barcode="8901262010048",
            cost_price=Decimal("46.00"), selling_price=Decimal("56.00"),
            current_quantity=Decimal("75.00"), unit_type="PIECE", categories=[groceries],
            image_url="/static/uploads/8901262010048.jpg"
        )

        all_products = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15]
        db.add_all(all_products)
        db.flush()

        # --- CUSTOMER LEDGER (🌟 NEW: real Customer rows for the Udhaar demo) ---
        print("🧾 Injecting Customer Khata Profiles...")
        gurpreet = models.Customer(
            name="Gurpreet Singh",
            phone="9812345678",
            total_credit_due=Decimal("0.00"),  # will be updated after order3 below
            credit_limit=Decimal("5000.00"),
            credit_block_mode="WARN",
        )
        db.add(gurpreet)
        db.flush()

        # --- AUDIT TRAIL LOGGING ---
        print("📜 Constructing Historical Stock Audits matching financial models...")
        now = datetime.datetime.now(datetime.timezone.utc)
        six_months_ago = now - datetime.timedelta(days=180)
        one_month_ago = now - datetime.timedelta(days=30)

        for prod in all_products:
            initial_qty = prod.current_quantity + Decimal("20.00")
            db.add(models.StockTransaction(
                product_id=prod.id,
                quantity_changed=initial_qty,
                type="INITIAL_STOCK",
                unit_cost=prod.cost_price,
                total_cost=initial_qty * prod.cost_price,
                notes="Opening balance allocation",
                timestamp=six_months_ago
            ))

        # --- FINANCIAL INVOICES & ORDERS SIMULATION ---
        print("🛒 Generating Distributed Revenue Metrics...")

        # ORDER 1: Cash Sale
        order1 = models.Order(
            total_amount=Decimal("416.00"), amount_paid=Decimal("416.00"), amount_pending=Decimal("0.00"),
            payment_method="CASH", payment_status="PAID", customer_info="Walk-in Customer", timestamp=one_month_ago
        )
        db.add(order1)
        db.flush()
        db.add(models.OrderItem(order_id=order1.id, product_id=p1.id, quantity=Decimal("10.00"), unit_price=Decimal("14.00")))
        db.add(models.OrderItem(order_id=order1.id, product_id=p11.id, quantity=Decimal("1.00"), unit_price=Decimal("240.00")))
        db.add(models.OrderItem(order_id=order1.id, product_id=p14.id, quantity=Decimal("2.00"), unit_price=Decimal("20.00")))
        p1.current_quantity -= Decimal("10.00")
        p11.current_quantity -= Decimal("1.00")
        p14.current_quantity -= Decimal("2.00")

        # ORDER 2: UPI Sale
        order2 = models.Order(
            total_amount=Decimal("1235.00"), amount_paid=Decimal("1235.00"), amount_pending=Decimal("0.00"),
            payment_method="ONLINE", payment_status="PAID", customer_info="Walk-in Customer", timestamp=now - datetime.timedelta(days=5)
        )
        db.add(order2)
        db.flush()
        db.add(models.OrderItem(order_id=order2.id, product_id=p3.id, quantity=Decimal("2.00"), unit_price=Decimal("175.00")))
        db.add(models.OrderItem(order_id=order2.id, product_id=p4.id, quantity=Decimal("10.00"), unit_price=Decimal("45.00")))
        db.add(models.OrderItem(order_id=order2.id, product_id=p9.id, quantity=Decimal("1.00"), unit_price=Decimal("331.00")))
        db.add(models.OrderItem(order_id=order2.id, product_id=p15.id, quantity=Decimal("2.00"), unit_price=Decimal("56.00")))
        p3.current_quantity -= Decimal("2.00")
        p4.current_quantity -= Decimal("10.00")
        p9.current_quantity -= Decimal("1.00")
        p15.current_quantity -= Decimal("2.00")

        # ORDER 3: Udhaar Deal (Partial Payment)
        # 🌟 FIX: now linked to a real Customer row (customer_id) instead of only a text
        # label, so the customer's total_credit_due and credit_limit are actually usable.
        order3 = models.Order(
            total_amount=Decimal("3298.00"), amount_paid=Decimal("1000.00"), amount_pending=Decimal("2298.00"),
            payment_method="PARTIAL", payment_status="PARTIAL",
            customer_id=gurpreet.id,
            customer_info="Gurpreet Singh (9812345678)",
            timestamp=now - datetime.timedelta(days=12)
        )
        db.add(order3)
        db.flush()
        db.add(models.OrderItem(order_id=order3.id, product_id=p6.id, quantity=Decimal("1.00"), unit_price=Decimal("2499.00")))
        db.add(models.OrderItem(order_id=order3.id, product_id=p5.id, quantity=Decimal("2.00"), unit_price=Decimal("399.00")))
        p6.current_quantity -= Decimal("1.00")
        p5.current_quantity -= Decimal("2.00")

        # 🌟 NEW: reflect the pending amount on the customer's running Udhaar balance
        gurpreet.total_credit_due = Decimal("2298.00")

        db.commit()
        print("🎉 Seeding Execution Finished! 15 products and 1 customer fully linked across your custom tables.")

    except Exception as e:
        db.rollback()
        print(f"❌ Transaction Lifecycle Crash during execution: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
