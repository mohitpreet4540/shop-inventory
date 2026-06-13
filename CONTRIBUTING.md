# Contributing Guide
Thanks for contributing to Shop Inventory.

## Contribution goals
When making changes, prioritize:
- Correct inventory and billing math
- Predictable API contracts
- Clear documentation updates
- Small, reviewable commits/PRs

## Local development workflow
1. Create a branch from `main`.
2. Run backend and optional frontend (see `docs/GETTING_STARTED.md`).
3. Make focused changes.
4. Manually validate the affected flow.
5. Update docs for behavioral/API/setup changes.
6. Open PR with clear summary and verification steps.

## Where to make changes
- API/business logic: `app/routers/`
- Data models: `app/models.py`
- Request/response validation: `app/schemas.py`
- DB/session config: `app/database.py`
- Frontend pages: `frontend/*.html`
- Frontend behavior/API calls: `frontend/js/*.js`
- Docs: `README.md`, `docs/*.md`

## Change patterns
### Adding a new endpoint
1. Define request/response schema in `app/schemas.py` if needed.
2. Implement route in the relevant `app/routers/*.py`.
3. If DB fields/tables change, update `app/models.py`.
4. Update API docs in `README.md`.
5. Add/extend manual test steps.

### Updating an existing API contract
1. Update schema validation first.
2. Update route logic.
3. Update any affected frontend JS calls.
4. Update docs examples and endpoint descriptions.

### Frontend-only changes
1. Update `frontend/*.html` and/or `frontend/js/*.js`.
2. Confirm calls still match backend payload/response shapes.
3. Verify billing, product, and category pages still load and work.

## Validation checklist (current project state)
- Backend starts without import/runtime errors.
- Swagger loads at `http://localhost:8000/docs`.
- Key flows pass manual test:
  - category creation/list
  - product creation/list
  - restock
  - checkout success/failure scenarios
  - search and stock ledger endpoints
- Frontend pages load and call APIs correctly.

## Documentation expectations
Include docs changes in the same PR if you modify:
- endpoint paths
- request/response payload shape
- environment variables
- startup commands
- user-facing workflow behavior

## Current known high-impact issues (good first fixes)
- Add backend endpoint for category page price edit action (`PUT /products/{id}/update-price`) or update frontend to use existing API.
- Remove or redesign duplicate product routes in `app/routers/dashboard.py`.
- Add automated tests (`pytest` + FastAPI `TestClient`).
- Introduce migration tooling (for example Alembic).

