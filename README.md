# Apna Bazar — Shop Inventory & Billing API

FastAPI-based retail inventory, billing, and credit-ledger backend for Indian kirana shops, with role-based access control and batch-level expiry tracking.

> **Status:** Backend is built and is the current focus. Frontend is under active development, not production-ready yet.

## Overview

A single-shop POS/ERP system built around three real problems small Indian retail shops actually have:

- **Udhaar (informal credit)** — customers buy on credit, shopkeeper tracks a running balance and can set a limit that either warns or hard-blocks further credit.
- **Perishable stock with staggered expiry dates** — the same product restocked on different days has different expiry dates sitting side by side on the shelf; the system tracks each delivery as its own batch and sells oldest-expiring stock first (FEFO).
- **Multiple staff roles at the counter** — owner, admin, and cashier accounts with different permissions, enforced via JWT auth.

## Features (implemented, not aspirational)

- **JWT authentication + RBAC** — `OWNER` / `ADMIN` / `CASHIER` roles, enforced on every route.
- **Udhaar credit ledger** — per-customer credit limit with configurable warn-or-block behavior.
- **Batch/expiry-aware inventory (FEFO)** — every restock is its own batch with its own expiry date; checkout consumes oldest-expiring stock first.
- **Stock correction with audit trail** — reconciling a physical count requires a reason and is logged; direct silent quantity edits are blocked.
- **Returns & refunds** — partial returns by line item, restockable vs. write-off (damaged) handling, refund via cash/online/credit adjustment.
- **Bulk CSV product import** — auto-creates missing categories, reports per-row success/failure.
- **Category tree** — two-level parent/child hierarchy with soft-deactivation.
- **Manual expense ledger** — non-inventory overheads (rent, utilities) tracked against net profit.
- **Concurrency-safe checkout** — row-level locking (`with_for_update()`) prevents double-selling the last unit.

## Tech Stack

- Python 3.11, FastAPI, SQLAlchemy 2.x, Pydantic v2
- PostgreSQL
- JWT auth (python-jose) + bcrypt password hashing (passlib)
- Docker + Docker Compose

## Project Structure

```
apna-bazar/
├── app/
│   ├── database.py       # SQLAlchemy engine/session
│   ├── dependencies.py   # JWT validation, role guards
│   ├── stock_utils.py    # Shared FEFO batch-consumption logic
│   ├── main.py            # App startup, router registration, schema patches
│   ├── models.py          # ORM models
│   ├── schemas.py         # Pydantic request/response schemas
│   └── routers/
│       ├── auth.py        # Login, user management
│       ├── categories.py
│       ├── products.py    # Products, restock, batches, bulk import, stock correction
│       ├── orders.py      # Checkout (FEFO consumption, credit limit enforcement)
│       ├── returns.py     # Returns & refunds
│       ├── customers.py   # Udhaar ledger, repayments
│       ├── finance.py     # Manual expense ledger
│       ├── reports.py     # Stock ledger, expiring-soon alerts
│       ├── search.py
│       └── dashboard.py   # Analytics
├── seed.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Setup

### 1) Create `.env`

```env
POSTGRES_USER=shop_admin
POSTGRES_PASSWORD=<choose-your-own>
POSTGRES_DB=shop_db
DATABASE_URL=postgresql://shop_admin:<same-password>@db:5432/shop_db
JWT_SECRET=<long-random-string>
```

### 2) Run

```bash
docker compose up --build
```

Load sample data (includes demo login accounts):
```bash
docker compose exec web_app python seed.py
```
Demo accounts: `owner/owner123`, `admin/admin123`, `cashier/cashier123` — **change these before any real deployment.**

## API Docs

Swagger UI: `http://localhost:8000/docs`

## Known Limitations

- No automated tests yet.
- No multi-branch support — single shop only, by design for now.
- Returns can't be traced back to the exact original batch a sale drew from (checkout may consume across multiple batches per sale); returned stock is re-added as a new batch instead.
- Frontend is not yet functional against this backend version.

## Roadmap

- Networking hardening / CORS lockdown for production
- Alembic migrations (currently uses idempotent `ALTER TABLE` patches at startup)
- Immutable audit log
- Automated tests (pytest + FastAPI TestClient)
