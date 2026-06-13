# Getting Started
This guide helps a new developer run the project end-to-end for the first time.

## What this project is
Shop Inventory is a FastAPI + PostgreSQL retail backend with a static frontend for:
- Inventory management
- Category management
- Billing/checkout with stock deduction
- Stock transaction ledger and product search

## Prerequisites
Choose one backend path:
- Docker + Docker Compose (recommended), or
- Python 3.11 + PostgreSQL 15

Also recommended:
- `curl` for quick API checks
- Modern browser for frontend pages

## 1) Clone and configure
Create `.env` in project root:

```env
POSTGRES_USER=shop_admin
POSTGRES_PASSWORD=shop_password
POSTGRES_DB=shop_db
DATABASE_URL=postgresql://shop_admin:shop_password@db:5432/shop_db
```

For local non-Docker backend, use:

```env
DATABASE_URL=postgresql://shop_admin:shop_password@localhost:5432/shop_db
```

## 2) Start backend
### Option A — Docker
```bash
docker compose up --build
```

### Option B — Local Python
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql://shop_admin:shop_password@localhost:5432/shop_db'
uvicorn app.main:app --reload
```

## 3) Optional: seed sample data
After DB and backend are up:

```bash
python seed.py
```

## 4) Open docs and UI
- Swagger: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Serve frontend:

```bash
python3 -m http.server 5500 --directory frontend
```

Then open:
- Billing: `http://localhost:5500/index.html`
- Inventory: `http://localhost:5500/products.html`
- Categories: `http://localhost:5500/categories.html`

## 5) Smoke test flow
1. Create category (`POST /categories/`)
2. Create product (`POST /products/`)
3. Place order (`POST /orders/`)
4. Verify stock changed (`GET /products/`)
5. Verify sale ledger (`GET /reports/stock-ledger/?transaction_type=SALE`)

## Common issues
### Backend cannot connect to DB
- Check `DATABASE_URL` host value (`db` in Docker, `localhost` in local run)
- Check DB container health with `docker compose logs -f db`

### Frontend page loads but API calls fail
- Confirm backend is running on `http://localhost:8000`
- Confirm frontend uses same base URL (`frontend/js/app.js`)

### Checkout gets rejected
- Ensure `total_amount` matches server-side computed total
- Ensure requested quantities are in stock
- For pending amount (`amount_pending > 0`), send non-anonymous `customer_info`

## Stop services
```bash
docker compose down
```
Or press `Ctrl+C` for local `uvicorn` / static server terminals.

