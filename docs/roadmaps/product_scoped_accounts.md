# Product-Scoped Accounts Implementation Roadmap

## Strategic Objectives

- **Guarantee product affinity on every Plaid integration path.** `PlaidAccount.product` must be non-null and aligned with the "product" dimension (e.g., `"transactions"`, `"investments"`).
- **Centralise provider orchestration behind explicit adapters.** `app/services/transactions.py` should depend on provider-specific helpers in `backend/app/providers/` to avoid import cycles and simplify testing.
- **Modularise helper utilities.** Split current monolithic helpers into per-product modules and surface a registry to drive product routes.
- **Raise coverage and documentation.** Tests and runbooks must demonstrate the product-scoped flow end-to-end so regressions are caught early.

## Guiding Regulations

1. **Schema invariants**
   - `PlaidAccount.product` is mandatory and constrained to the enum `{"transactions", "investments", "liabilities"}`. Add an Alembic migration enforcing `nullable=False` and a `CHECK` constraint (`accounts_product_check`).
   - For legacy rows, backfill using `PlaidItem.product` when present; otherwise default to `"transactions"`.
2. **API contracts**
   - `/api/plaid/transactions/exchange` must persist the product inferred from the Plaid item metadata. Fail the request with `422` if the payload lacks a resolvable product.
   - `/api/products/{product}/transactions/sync` returns `{ "updated": bool, "errors": list[str] }` and always sets HTTP 200. Provider failures populate `errors` while keeping `updated` `False`.
3. **Provider adapter rules**
   - Adapter functions must expose the signature `async def sync_transactions(account_id: UUID, *, user_id: UUID) -> SyncResult`.
   - Each adapter handles provider-specific retries/backoff internally and raises `ProviderSyncError` for fatal failures.
4. **Helper module governance**
   - Every helper module exports a `RegistryEntry` dataclass with `product`, `sync`, and `serialize_account` attributes.
   - Registry lives in `backend/app/helpers/plaid/__init__.py` and is consumed by services.
5. **Testing & observability**
   - Pytest modules must cover success, validation failure, and provider error branches. Minimum coverage for new modules: 90% line coverage (`pytest --cov=backend/app --cov-report=term-missing`).
   - Emit structured logs (`logger.info("sync_complete", extra={"product": product, "account_id": str(account_id)})`).

## Phase 1 – Enforce Product Tagging

### Code Changes

1. Update `backend/app/routes/plaid_transactions.py`:
   ```python
   product = payload.product or plaid_item.product
   if product is None:
       raise HTTPException(status_code=422, detail="Missing Plaid product")
   saved_account = account_logic.save_plaid_account(
       db_session=session,
       plaid_account=plaid_account,
       user_id=current_user.id,
       product=product,
   )
   ```
2. Adjust `backend/app/models/plaid_account.py` model to enforce the enum constraint using `sqlalchemy.Enum`.
3. Generate Alembic migration `backend/migrations/versions/<timestamp>_enforce_plaid_account_product.py`:
   - Add `op.alter_column("plaid_accounts", "product", existing_type=sa.String(), nullable=False)`.
   - Create `sa.CheckConstraint` ensuring the enum values.
   - Backfill legacy rows via an inline `UPDATE` statement selecting from `plaid_items`.

### Tests

- Expand `tests/routes/test_plaid_transactions_exchange.py` to assert the product is persisted and to verify a `422` when the product is missing.
- Add migration test in `tests/migrations/test_plaid_account_product.py` to confirm backfill logic.

### Documentation

- Update `docs/maintenance/deprecated/backend-routing-plan.md` to reflect the non-null constraint and error behaviour.

## Phase 2 – Provider Transaction Adapters

### Code Changes

1. Create `backend/app/providers/__init__.py` exporting `ProviderRegistry` and `SyncResult` dataclasses.
2. Implement `backend/app/providers/plaid.py`:

   ```python
   from backend.app.helpers.plaid.transactions import sync_transactions as plaid_sync

   async def sync_transactions(account_id: UUID, *, user_id: UUID) -> SyncResult:
       refreshed = await plaid_sync(account_id=account_id, user_id=user_id)
       return SyncResult(updated=refreshed.updated, errors=refreshed.errors)
   ```

3. Refactor `backend/app/services/transactions.py` to select adapters via `ProviderRegistry.for_account(account)` and to normalise responses.
4. Update `backend/app/routes/product_transactions.py` to propagate adapter errors:
   ```python
   result = await transactions_service.sync_product(product=product, account_id=account_id, user=current_user)
   return JSONResponse(status_code=200, content=result.model_dump())
   ```

### Tests

- Introduce `tests/services/test_transactions_service.py` covering Plaid success/error paths using fixtures with fake adapters.
- Add route-level tests in `tests/routes/test_product_transactions.py` mocking the service layer.

### Documentation

- Document adapter responsibilities in `docs/backend/providers.md`, including error classes and retry policies.

## Phase 3 – Modular Plaid Helpers

### Code Changes

1. Split `backend/app/helpers/plaid_helpers.py` into:
   - `helpers/plaid/accounts.py`
   - `helpers/plaid/transactions.py`
   - `helpers/plaid/investments.py`
2. Introduce `helpers/plaid/__init__.py`:
   ```python
   REGISTRY: dict[str, RegistryEntry] = {
       "transactions": RegistryEntry(product="transactions", sync=transactions.sync_transactions, serialize_account=accounts.serialize),
       "investments": RegistryEntry(product="investments", sync=investments.sync_positions, serialize_account=accounts.serialize_investment),
   }
   ```
3. Refactor `account_logic.refresh_data_for_plaid_account` to call `REGISTRY[product].sync(...)` instead of importing functions directly.
4. Update investment logic to import from `helpers/plaid/investments.py`.

### Tests

- Create `tests/helpers/plaid/test_transactions_helper.py` validating pagination, cursor handling, and error wrapping.
- Mirror tests for investments and accounts helpers.

### Documentation

- Add module overviews to each helper file and update `docs/backend/plaid_helpers.md` describing registry usage.

## Phase 4 – Documentation & Runbooks

### Tests & Automation

- Add API integration test `tests/integration/test_product_sync_flow.py` walking through: link account → enforce product → invoke `/api/products/<product>/transactions/sync` → assert transactions stored.
- Ensure `pytest --cov=backend/app --cov-report=term-missing` runs in CI and gate merges at ≥85% overall coverage.

### Documentation

- Extend `docs/roadmaps/product_scoped_accounts.md` (this file) with update timestamps.
- Update `docs/process/release_checklist.md` with migration and verification steps.
- Publish operator runbook `docs/maintenance/product_account_backfill.md` including commands:
  ```bash
  flask db upgrade
  flask shell -c "from app.scripts.backfill_products import run; run(dry_run=False)"
  flask shell -c "from app.models import PlaidAccount; assert PlaidAccount.query.filter_by(product=None).count() == 0"
  ```

### Monitoring

- Configure alerts in `scripts/alerts/product_sync.yaml` verifying `sync_complete` logs appear hourly per product.
- Add Grafana dashboard panels charting `sync_latency_seconds` and `sync_error_total` metrics.

## Timeline & Dependencies

| Milestone        | Target Sprint | Dependencies                |
| ---------------- | ------------- | --------------------------- |
| Phase 1 complete | Sprint 25.03  | Alembic migrations reviewed |
| Phase 2 complete | Sprint 25.04  | Phase 1 data guarantees     |
| Phase 3 complete | Sprint 25.05  | Phase 2 service registry    |
| Phase 4 complete | Sprint 25.06  | All previous phases         |

## Acceptance Criteria

1. No `plaid_accounts` row exists without a product value after migration.
2. `/api/products/<product>/transactions/sync` returns deterministic JSON and logs structured telemetry.
3. Helper registry allows adding a new product with <50 LoC changes.
4. CI enforces coverage and lint checks for newly introduced modules.

_Last updated: 2025-10-03_
