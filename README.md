# Shop Inventory API
FastAPI-based backend for managing shop categories, products, orders, stock movements, and finance entries.

## What this project is
This project is a small ERP-style backend for a retail shop. It provides APIs to:
- Create and list product categories
- Create and list products
- Checkout orders with stock validation
- Automatically log stock and finance records during checkout

## Tech stack (what is used)
- Python 3.11
- FastAPI
- Uvicorn
- SQLAlchemy 2.x
- PostgreSQL (via `psycopg2-binary`)
- Docker + Docker Compose

Dependencies are listed in `requirements.txt`.

## Project structure (what each file does)
- `app/main.py`
  - FastAPI app
  - Pydantic request/response schemas
  - API endpoints (`/`, `/categories/`, `/products/`, `/orders/`)
  - Main checkout business logic
- `app/models.py`
  - SQLAlchemy models:
    - `Category`
    - `Product`
    - `Order`
    - `OrderItem`
    - `StockTransaction`
    - `FinanceLedger`
- `app/database.py`
  - Database engine/session setup
  - Base declarative model class
- `Dockerfile`
  - Container image for the API service
- `docker-compose.yml`
  - Multi-container setup for API + PostgreSQL
- `requirements.txt`
  - Python package dependencies

## Setup and run
You can run this project with Docker (recommended) or locally.

### Option 1: Docker (recommended)
1. Build and start services:
   - `docker compose up --build`
2. API will be available at:
   - `http://localhost:8000`
3. Swagger UI:
   - `http://localhost:8000/docs`

To stop:
- `docker compose down`

To stop and remove DB volume (fresh reset):
- `docker compose down -v`

### Option 2: Local Python setup
1. Create and activate virtual environment:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Set database URL (PostgreSQL must be running):
   - `export DATABASE_URL='postgresql://shop_admin:shop_password@localhost:5432/shop_db'`
4. Run server:
   - `uvicorn app.main:app --reload`

## API quick usage
### Health
- `GET /`

### Categories
- `POST /categories/`
- `GET /categories/`

### Products
- `POST /products/`
- `GET /products/`

### Orders / Checkout
- `POST /orders/`

Example checkout request:
`curl -X POST 'http://localhost:8000/orders/' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{"payment_method":"online","items":[{"product_id":2,"quantity":1}]}'`

## Testing
### Current status
There are no automated test files in this repository yet (`pytest` tests are not present).

### How to test right now
Use one of these methods:
- Swagger UI: `http://localhost:8000/docs`
- Manual curl/API client calls for endpoint validation

Recommended manual flow:
1. Create category
2. Create product linked to category
3. Checkout order via `/orders/`
4. Verify product stock decreased and order created

### Add automated tests (recommended next step)
Suggested:
- Add `pytest`
- Add API tests with FastAPI `TestClient`
- Add integration tests for checkout success/failure scenarios

## Notes
- Monetary values now use decimal-safe handling in checkout flow to avoid float/decimal mismatch errors.
- For production, move credentials from compose file to environment variables/secrets.
