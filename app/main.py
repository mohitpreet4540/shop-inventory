from fastapi import FastAPI
from app.database import engine
from app.models import Base
from fastapi.middleware.cors import CORSMiddleware
# Import your clean modular components
from app.routers import categories, products, orders ,dashboard ,reports,search

# Ensure database tables map correctly on service startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Universal Shop ERP Engine", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your frontend HTML files to talk to the backend safely
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, PUT, DELETE
    allow_headers=["*"],  # Allows all headers
)

# Mount your clean sub-routers cleanly
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(search.router)

@app.get("/")
def read_root():
    return {
        "status": "Online", 
        "architecture": "Modular APIRouter Execution Engine",
        "documentation": "/docs"
    }


