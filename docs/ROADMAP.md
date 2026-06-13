# Project Roadmap
This roadmap communicates the likely direction of the project so newcomers can contribute with context.

## Product vision
Build a reliable, small-shop ERP/POS backend with a simple UI that supports:
- accurate inventory tracking
- fast billing and barcode-assisted checkout
- transparent stock movement audit history
- practical credit/partial-payment workflows

## Current state snapshot
- Core category/product/order/search/report APIs are present.
- Static frontend pages provide billing, inventory, and category operations.
- Decimal-based money/quantity math is used in backend models and checkout.
- Gaps remain in test coverage, migration strategy, and endpoint consistency.

## Near-term priorities (Now)
1. Fix backend/frontend contract mismatches:
   - implement or remove `PUT /products/{id}/update-price` usage
   - resolve duplicate `/products` router overlap (`products.py` vs `dashboard.py`)
2. Add automated tests for checkout and stock safety critical paths.
3. Harden CORS/config defaults for safer deployment behavior.
4. Clean up timestamp consistency (timezone-aware everywhere).

## Mid-term priorities (Next)
1. Introduce DB migrations (Alembic) and schema versioning discipline.
2. Add role/auth controls for privileged inventory operations.
3. Add reporting enhancements (date filters, summary metrics endpoints).
4. Improve frontend UX consistency and error handling polish.

## Long-term direction (Later)
1. Advanced analytics dashboard (sales trends, low-stock forecasting).
2. Export workflows (CSV/PDF invoices and stock ledgers).
3. Multi-store or tenant-ready data model evolution.
4. Observability improvements (structured logs, health checks, metrics).

## What contributors can pick up first
- API consistency fixes
- tests and validation coverage
- documentation alignment updates
- frontend/backend integration bugs

## How this roadmap should be used
- Treat this as a living document.
- Update it when priorities shift.
- Link roadmap items to PRs/issues as work is completed.

