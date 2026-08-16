import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time

from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.database import engine
from app.models import Base


from app.routers import auth, categories, products, orders, dashboard, reports, search, customers, finance ,returns




def init_db():
    maxretries = 10
    delay = 2
    for atempt in range(1, maxretries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception as e:
            if atempt == maxretries:
                print("Could not connect to database ")
                raise e
            print(f"waiting for database (attempt {atempt}/{maxretries})...")
            time.sleep(delay)
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  
    yield

app = FastAPI(title="Shop ERP engine",lifespan=lifespan )


_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allow_origins = ["*"] if _origins_env.strip() == "*" else [o.strip() for o in _origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# handles local images Safely
if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

#  INCLUDE MODULAR SUB-ruoter
app.include_router(auth.router)  
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(customers.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(search.router)
app.include_router(finance.router)
app.include_router(returns.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
       
    }
