# Architecture Overview
This document explains how the project is structured and where to make changes.

## High-level components
- Backend API: FastAPI app in `app/`
- Database: PostgreSQL with SQLAlchemy ORM models
- Frontend: static HTML + JS in `frontend/`, calling backend APIs

## Backend layout
- Entry point: `app/main.py`
  - Creates app
  - Registers routers
  - Configures CORS
  - Calls `Base.metadata.create_all(...)` on startup
- Database wiring: `app/database.py`
  - `DATABASE_URL`, SQLAlchemy engine, session factory, `get_db` dependency
- Data models: `app/models.py`
  - `Category`, `Product`, `Order`, `OrderItem`, `StockTransaction`, `FinanceLedger`
- Request/response schemas: `app/schemas.py`
  - Validation for create/list/search/checkout/reports

## Router boundaries
- `app/routers/categories.py`
  - `GET /categories/`
  - `POST /categories/`
- `app/routers/products.py`
  - `GET /products/`
  - `POST /products/`
  - `POST /products/add-stock/`
- `app/routers/orders.py`
  - `POST /orders/`
- `app/routers/reports.py`
  - `GET /reports/stock-ledger/`
- `app/routers/search.py`
  - `GET /search/products/`

## Data model relationships
- Category 1:N Product (`Product.category_id`)
- Order 1:N OrderItem (`OrderItem.order_id`)
- Product references in OrderItem and StockTransaction
- Stock movements tracked in `stock_transactions`

## Checkout flow (current implementation)
1. Client sends cart items and payment split fields.
2. Backend resolves product by `product_id` or `barcode`.
3. Backend validates stock and recomputes total.
4. Backend validates `total_amount` and payment split math.
5. Backend creates `Order`, `OrderItem` rows.
6. Backend deducts stock and writes `SALE` stock transactions.

## Frontend structure
- `frontend/index.html` + `frontend/js/billing.js`
  - barcode scan/manual search cart workflow
- `frontend/products.html` + `frontend/js/products.js`
  - create product, list inventory, quick restock
- `frontend/categories.html` + `frontend/js/categories.js`
  - create/list categories and category product preview
- `frontend/js/app.js`
  - shared `API_BASE_URL` and API error helper

## How to choose where to change code
- New API behavior:
  - model change (`models.py`) if schema changes
  - validation change (`schemas.py`)
  - endpoint logic (`routers/*.py`)
  - update docs (`README.md`, `docs/*`)
- Frontend behavior:
  - page markup (`frontend/*.html`)
  - interactions/API calls (`frontend/js/*.js`)

## Known architecture gaps
- `app/routers/dashboard.py` duplicates product-style routes under `/products`.
- `frontend/js/categories.js` calls update-price endpoint not implemented on backend.
- No migration tool yet (schema is created directly at startup).
- No automated test suite yet.

