# Apna Bazar — Frontend

A fresh static frontend for your current `apna-bazar` FastAPI backend (JWT auth,
role-based access, product/category/customer/finance/reports routers).

## Running it

1. Start your backend (`docker compose up`, or `uvicorn app.main:app --reload`),
   confirm it's on `http://localhost:8000`.
2. Serve this folder as static files — don't open the HTML files directly with
   `file://`, since `fetch()` calls are more reliable over `http://`:
   ```bash
   cd apna-bazar-frontend
   python3 -m http.server 5500
   ```
   Then open `http://localhost:5500/login.html`.
3. If your backend runs somewhere other than `localhost:8000`, set it before the
   other scripts load — add this line right before the `core.js` `<script>` tag
   on every page:
   ```html
   <script>window.API_BASE_URL = "https://your-backend-host";</script>
   ```
4. Make sure your backend's `ALLOWED_ORIGINS` env var includes the origin you're
   serving the frontend from (or leave it as `*` for local development).

## First-time setup

There's no seeded account. On `login.html`, use **"First time setting up this
shop? Create the owner account"** — this calls `POST /api/auth/bootstrap-owner`,
which only works once, before any OWNER exists. After that, sign in as the
owner and add ADMIN/CASHIER accounts from **Staff Accounts**.

## Pages → backend routes

| Page | Routes used | Roles |
|---|---|---|
| `login.html` | `/api/auth/login`, `/api/auth/bootstrap-owner` | anyone |
| `index.html` (Dashboard) | `/api/dashboard/analytics` | OWNER, ADMIN |
| `billing.html` (POS) | `/api/search/products`, `/api/products/lookup/{barcode}`, `/api/customers/`, `/api/orders/` | all roles |
| `products.html` | `/api/products/*`, `/api/categories/tree` | all roles view; OWNER/ADMIN manage |
| `categories.html` | `/api/categories/*` | all roles view; OWNER/ADMIN manage |
| `customers.html` | `/api/customers/*` | all roles; credit settings need OWNER/ADMIN |
| `finance.html` | `/api/finance/expenses*` | OWNER, ADMIN |
| `reports.html` | `/api/reports/stock-ledger` | OWNER, ADMIN |
| `users.html` | `/api/auth/users*` | OWNER only |

## A gap to know about

Your backend has no `GET /api/orders/` (or `GET /api/orders/{id}`) — only
`POST /api/orders/` to create a sale. So there's currently no order-history
or past-receipts page here, because there's no endpoint to back it with. The
billing page still shows a toast confirming each sale (order id, total,
change due, any credit warning) right after checkout. If you want a sales
history page, that'll need a list endpoint added to `orders.py` first — happy
to help with that when you're ready.

## Design

Ink-navy app chrome, cream "ledger paper" cards for khata/customer balances,
and a receipt-styled cart on the billing page — khata-red flags amounts owed,
settled-green flags cleared balances. Fonts: Roboto Slab for headings/numbers,
IBM Plex Sans for UI text, IBM Plex Mono for money and barcodes. All loaded
from Google Fonts + Tailwind/Font Awesome CDNs, so you'll need internet access
the first time each page loads (fonts/icons are cached after that).
