import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text  # 🌟 CRITICAL: Added for the schema patch

from app.database import engine
from app.models import Base
from app.routers import categories, products, orders, dashboard, reports, search, customers

# Ensure database tables map correctly on service startup
Base.metadata.create_all(bind=engine)

# =================================================================
# 🌟 AUTOMATIC DATABASE PATCH (Safely injects missing columns)
# =================================================================
with engine.connect() as conn:
    try:
        # Adds the missing column to the existing table without data loss
        conn.execute(text("ALTER TABLE categories ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;"))
        conn.commit()
        print("Backend Patch Success: 'is_active' column verified in 'categories' table.")
    except Exception as e:
        print(f"Patch skipped or handled: {str(e)}")

app = FastAPI(title="Universal Shop ERP Engine", version="2.0.0")

# 1. CORS MIDDLEWARE SETUP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your frontend dashboard files to talk to the backend safely
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],  # Allows all headers
)

# 2. LOCAL ASSET SERVICE MOUNT (Handles Local Images Safely)
if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3. INCLUDE MODULAR SUB-ROUTERS
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(customers.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(search.router)

# 4. ROOT HEALTH ENDPOINT
@app.get("/")
def read_root():
    return {
        "status": "Online", 
        "architecture": "Modular APIRouter Execution Engine",
        "documentation": "/docs"
    }