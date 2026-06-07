from fastapi import FastAPI
from app.database import engine
from app.models import Base
# Import your clean modular components
from app.routers import categories, products, orders ,dashboard

# Ensure database tables map correctly on service startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Universal Shop ERP Engine", version="2.0.0")

# Mount your clean sub-routers cleanly
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(dashboard.router)


@app.get("/")
def read_root():
    return {
        "status": "Online", 
        "architecture": "Modular APIRouter Execution Engine",
        "documentation": "/docs"
    }


