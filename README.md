# Shop Inventory API
FastAPI-based retail inventory and billing backend with a static frontend for billing, product management, and category management.
## Documentation
- `README.md` (this file): project summary, setup, run, API basics
- `docs/README.md`: documentation hub and recommended reading order
- `docs/GETTING_STARTED.md`: newcomer setup + first-run walkthrough
- `docs/ARCHITECTURE.md`: backend/frontend/data architecture overview
- `CONTRIBUTING.md`: how to make changes and contribute safely
- `docs/ROADMAP.md`: current direction and planned improvements

## Overview
This project provides a small ERP/POS workflow with:
- Category management (including optional parent-child hierarchy)
- Product management with barcode, brand, unit type, pricing, and decimal stock quantity
- Billing checkout flow with stock validation and split-payment ledger values (`total_amount`, `amount_paid`, `amount_pending`)
- Stock transaction audit logs (`INITIAL_STOCK`, `RESTOCK`, `SALE`)
- Search API used by barcode scanner/manual search in the frontend
- Frontend pages for billing (`frontend/index.html`), inventory (`frontend/products.html`), and categories (`frontend/categories.html`)

## Tech stack
- Python 3.11
- FastAPI + Uvicorn
- SQLAlchemy 2.x
- Pydantic v2
- PostgreSQL (`psycopg2-binary`)
- Docker + Docker Compose
- HTML + Tailwind CDN + Vanilla JavaScript frontend

## Project structure
```text
shop-inventory/
├── app/
│   ├── database.py          # SQLAlchemy engine/session setup
│   ├── main.py              # FastAPI app startup and router registration
│   ├── models.py            # ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   └── routers/
│       ├── categories.py    # Category APIs
│       ├── products.py      # Product + restock APIs
│       ├── orders.py        # Checkout/order APIs
│       ├── reports.py       # Ledger/report APIs
│       ├── search.py        # Product search APIs
│       └── dashboard.py     # Duplicate product-like router (see Notes)
├── frontend/
│   ├── index.html
│   ├── products.html
│   ├── categories.html
│   ├── css/
│   │   └── styles.css
│   └── js/
│       ├── app.js
│       ├── billing.js
│       ├── categories.js
│       └── products.js
├── seed.py                  # Sample data seeding script
├── CONTRIBUTING.md          # Contribution and change workflow
├── docs/
│   ├── README.md            # Documentation index
│   ├── GETTING_STARTED.md   # Newcomer runbook
│   ├── ARCHITECTURE.md      # System design and request flow
│   └── ROADMAP.md           # Project direction and priorities
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

For local (non-Docker) backend runs, use `localhost` in `DATABASE_URL`:

```env
DATABASE_URL=postgresql://shop_admin:shop_password@localhost:5432/shop_db
```

## Run the app
### Option A: Docker (recommended)
```bash
docker compose up --build
```

Useful commands:
```bash
docker compose logs -f web_app
docker compose logs -f db
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

Frontend (optional but recommended):
```bash
python3 -m http.server 5500 --directory frontend
```
Then open `http://localhost:5500`.

To load sample data (after DB is reachable):
```bash
python seed.py
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
- `POST /products/add-stock/` - increase stock and optionally update cost/selling prices
- `POST /orders/` - create checkout order and deduct stock
- `GET /reports/stock-ledger/` - stock transaction ledger
  - Optional query: `transaction_type` (`INITIAL_STOCK`, `RESTOCK`, `SALE`)
- `GET /search/products/?query=<text>` - product search by name, brand, or exact barcode

## Example checkout request
```bash
curl -X POST 'http://localhost:8000/orders/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "payment_method": "CASH",
    "total_amount": 1200.00,
    "amount_paid": 1200.00,
    "amount_pending": 0.00,
    "customer_info": "Walk-in Customer",
    "items": [
      {
        "product_id": 1,
        "quantity": 1.00
      }
    ]
  }'
```

Important: `total_amount` must match the backend-calculated total from product selling prices and quantities.

## Testing
### Current status
Automated tests are not present in this repository yet.

### Manual testing flow
1. Start backend (`docker compose up --build` or local `uvicorn`).
2. Create a category (`POST /categories/`).
3. Create a product (`POST /products/`) under that category.
4. Search product (`GET /search/products/?query=...`) or use frontend pages.
5. Place an order (`POST /orders/`) with matching total/paid/pending values.
6. Confirm stock decreases in `GET /products/`.
7. Confirm sale entry appears in `GET /reports/stock-ledger/?transaction_type=SALE`.

### Recommended next step
Add automated tests (`pytest` + FastAPI `TestClient`) for:
- Category duplicate prevention
- Product creation and barcode uniqueness checks
- Restock workflow including optional price updates
- Checkout success and failure scenarios (stock shortfall, mismatched totals, invalid cart item)
- Search and reports endpoint behavior

## Notes
- Money and quantity fields use `Decimal`/`Numeric` types to avoid floating-point errors.
- `.env` is intentionally ignored via `.gitignore`.
- `app/main.py` uses `Base.metadata.create_all(...)`, so tables are auto-created on startup (no migration tool configured yet).
- `frontend/js/categories.js` calls `PUT /products/{id}/update-price`, but this endpoint is not currently implemented in backend routers.
- `app/routers/dashboard.py` currently duplicates `products` routes under the same `/products` prefix and does not expose separate dashboard analytics endpoints.
- For deeper onboarding, see `docs/README.md` and `CONTRIBUTING.md`.
