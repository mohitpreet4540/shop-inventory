# Shop Inventory API
FastAPI backend for managing categories, products, order checkout, stock transactions, and finance ledger entries.

## Overview
This project provides a simple ERP-style inventory service with:
- Category management (including parent-child categories)
- Product management with stock quantity
- Checkout endpoint that validates stock, creates order + order items, reduces stock, and writes ledger records
- Decimal-safe money calculations for financial values

## Tech stack
- Python 3.11
- FastAPI + Uvicorn
- SQLAlchemy 2.x
- PostgreSQL (`psycopg2-binary`)
- Docker + Docker Compose (with DB healthcheck)

## Project structure
```text
shop-inventory/
├── app/
│   ├── database.py      # SQLAlchemy engine/session setup
│   ├── main.py          # FastAPI app, schemas, and API routes
│   └── models.py        # ORM models
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Setup
### 1) Create `.env` file
Create a `.env` file in the project root:

```env
POSTGRES_USER=shop_admin
POSTGRES_PASSWORD=shop_password
POSTGRES_DB=shop_db
DATABASE_URL=postgresql://shop_admin:shop_password@db:5432/shop_db
```

## Run the app
### Option A: Docker (recommended)
```bash
docker compose up --build
```

Useful commands:
```bash
docker logs -f shop_backend
docker compose down
docker compose down -v
```

### Option B: Local Python
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql://shop_admin:shop_password@localhost:5432/shop_db'
uvicorn app.main:app --reload
```

## API docs
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## API endpoints
- `GET /` - service status
- `POST /categories/` - create category
- `GET /categories/` - list categories
- `POST /products/` - create product
- `GET /products/` - list products
- `POST /orders/` - checkout order

## Example checkout request
```bash
curl -X POST 'http://localhost:8000/orders/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "payment_method": "online",
    "items": [
      {
        "product_id": 2,
        "quantity": 1
      }
    ]
  }'
```

## Testing
### Current status
Automated tests are not added yet.

### Manual testing flow
1. Create a category (`POST /categories/`)
2. Create a product (`POST /products/`) using that category
3. Place an order (`POST /orders/`)
4. Confirm stock is reduced in `GET /products/`

### Recommended next step
Add automated tests with `pytest` + FastAPI `TestClient` for:
- Successful checkout
- Out-of-stock checkout
- Empty cart validation
- Invalid product ID handling

## Notes
- Money fields are handled with `Decimal` in the checkout path to avoid float precision issues.
- Keep `.env` out of version control (`.gitignore` already includes it).
