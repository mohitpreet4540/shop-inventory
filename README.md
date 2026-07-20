# Shop Inventory & SaaS ERP API

FastAPI-based retail inventory, multi-branch billing, and authorization backend with a static frontend for billing, product management, and category management.

> **Status:** Backend is built and is the current focus. Frontend is not working yet — it's planned for future development.

## Documentation

- **README.md** (this file): project summary, setup, run, API basics
- **docs/README.md**: documentation hub and recommended reading order
- **docs/GETTING_STARTED.md**: newcomer setup + first-run walkthrough
- **docs/ARCHITECTURE.md**: backend/frontend/data architecture overview
- **CONTRIBUTING.md**: how to make changes and contribute safely
- **docs/ROADMAP.md**: current direction and planned improvements

## Overview

This project provides a SaaS-ready small ERP/POS multi-tenant workflow with:

- **Role-Based Access Control (RBAC)**: Secure JWT authentication supporting `OWNER`, `ADMIN`, and `CASHIER` privileges.
- **SaaS Feature Flagging**: Centralized settings panel to enable/disable specific premium features (e.g., multi-branch tracking, structural bulk actions).
- **Multi-Branch Inventory Architecture**: Centralized master directory capable of handling stock levels isolated by individual physical branch locations.
- **Flexible Credit Limit Safeguards (Udhaar Ceilings)**: Customer profile limits featuring customizable options to either completely block transactions or trigger soft alerts on overages.
- **Dynamic Bulk Imports**: Automated schema extraction pipelines engineered to map, match, and register incoming batch product spreadsheets natively.
- **Category Management**: Nested parent-child tree mapping limiting depths to a neat two-level hierarchy.
- **Billing Checkout Flow**: Concurrency row-locking (`with_for_update()`) safeguarding inventory changes against split-payment tallies.
- **Double-Entry Financial Accounting**: Centralized revenue logging linking wholesale procurement, store overhead, and manual debt repayments to automated expense indices.

## Tech Stack

- Python 3.11
- FastAPI + Uvicorn
- SQLAlchemy 2.x
- Pydantic v2
- PyJWT / Python-Jose (HMAC SHA-256 Token Encryption)
- PostgreSQL (psycopg2-binary)
- Docker + Docker Compose
- HTML + Tailwind CDN + Vanilla JavaScript frontend

## Project Structure

```
shop-inventory/
├── app/
│   ├── database.py          # SQLAlchemy engine/session setup
│   ├── dependencies.py      # JWT validation routines and role-checking guards
│   ├── main.py              # FastAPI app startup and router registration
│   ├── models.py            # ORM models (Users, Branches, Stocks, Ledger, Khata)
│   ├── schemas.py           # Pydantic request/response validation contracts
│   └── routers/
│       ├── auth.py          # Session registration and JWT issuance
│       ├── categories.py    # Category APIs and tree builders
│       ├── products.py      # Product, local branch restocking, and bulk import APIs
│       ├── orders.py        # Secure checkout/order transactional engines
│       ├── reports.py       # Ledger/report APIs
│       ├── search.py        # Global product preview search APIs
│       ├── customers.py     # Customer Khata, credit allocation, and debt repayment APIs
│       └── finance.py       # Out-of-pocket overhead manual expense logs
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

### 1) Create `.env` File

Create a `.env` file in the project root:

```env
POSTGRES_USER=shop_admin
POSTGRES_PASSWORD=shop_password
POSTGRES_DB=shop_db
DATABASE_URL=postgresql://shop_admin:shop_password@db:5432/shop_db
JWT_SECRET=super_secret_signing_key_9988
```

For local (non-Docker) backend runs, use `localhost` in `DATABASE_URL`:

```env
DATABASE_URL=postgresql://shop_admin:shop_password@localhost:5432/shop_db
```

### Run the App

#### Option A: Docker (Recommended)

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

#### Option B: Local Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql://shop_admin:shop_password@localhost:5432/shop_db'
export JWT_SECRET='super_secret_signing_key_9988'
uvicorn app.main:app --reload
```

Frontend (optional but recommended):

```bash
python3 -m http.server 5500 --directory frontend
```

Then open [http://localhost:5500](http://localhost:5500).

To load sample data (after the DB is reachable):

```bash
python seed.py
```

## API Docs

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Service status |
| POST | `/api/auth/login` | Authenticate user and return secure JWT credentials |
| POST | `/api/categories/` | Create category |
| GET | `/api/categories/tree` | Fetch real-time multi-level hierarchical category navigation tree |
| POST | `/api/products/` | Create product entry |
| POST | `/api/products/bulk-import` | Batch insert rows, auto-allocate missing categories, and seed branch stocks |
| GET | `/api/products/` | List comprehensive warehouse master ledger filtered via dual-sieve methods |
| POST | `/api/products/{id}/restock` | Wholesale acquisition ingestion logging automated out-of-pocket expenses |
| PATCH | `/api/products/{id}` | Dynamic, frontend-driven structural updates for item master data |
| POST | `/api/orders/` | Secured transactional POS checkout handling concurrency locking and customer debt validation |
| POST | `/api/customers/` | Provision a new ledger identity complete with personalized debt limits |
| POST | `/api/customers/{id}/repay` | Clear outstanding Udhaar dues using atomic double-entry bookkeeping |
| POST | `/api/finance/expenses` | Manually submit recurring operational retail costs |
| GET | `/api/search/products/?q=<text>` | Instant index matches for brand name, title, or barcode scanner string values |

### Example Checkout Request

```bash
curl -X POST 'http://localhost:8000/api/orders/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_jwt_access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "payment_method": "CREDIT",
    "amount_paid": 0.00,
    "payment_status": "UNPAID",
    "customer_id": 4,
    "customer_info": "Regular Credit Customer",
    "items": [
      {
        "product_id": 12,
        "quantity": 2.00
      }
    ]
  }'
```

> **Important:** The system automatically reads active values from the item directory to derive checkout validation criteria, balance statements, and customer record balances.

## Testing

### Current Status

Automated tests are not present in this repository yet.

### Manual Testing Flow

1. Start backend (`docker compose up --build` or local `uvicorn`).
2. Generate an access token via the login endpoint (`POST /api/auth/login`).
3. Add a category profile via the authenticated management router (`POST /api/categories/`).
4. Inject items individually (`POST /api/products/`) or invoke the bulk importer (`POST /api/products/bulk-import`).
5. Create a customer profile with an optional `credit_limit` rule and set the warning/blocking preferences.
6. Trigger order executions (`POST /api/orders/`) and evaluate how the core handles limits when payments run short.
7. Confirm ledger balances reflect automated tracking shifts across both stock registries and financial expense ledgers.

### Recommended Next Steps

Add automated tests (pytest + FastAPI TestClient) for:

- Role authorization boundaries (ensuring cashiers are locked out of admin dashboard routers)
- Credit limit edge cases (testing blocking states versus soft warning actions during checkout)
- Multi-branch data boundaries (verifying branch stock actions do not mutate other store locations)
- Bulk parsing accuracy under high-volume load conditions
- Concurrent race conditions across checkouts using multiple parallel threads

## Notes

- Money and quantity fields use `Decimal`/`Numeric` types to avoid floating-point errors.
- `.env` is intentionally ignored via `.gitignore`.
- `app/main.py` uses automatic database patches to dynamically alter structural adjustments (such as the category `is_active` flag) on service initialization.
- Relational mapping dependencies feature a hard constraint protection hierarchy (`ondelete="RESTRICT"`) on active order rows to ensure core billing history remains clean and protected against accidental deletions.
