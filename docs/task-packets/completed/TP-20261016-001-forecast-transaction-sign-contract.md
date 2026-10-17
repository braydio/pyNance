# TP-20261016-001: Forecast Transaction Sign Contract and Reconciliation

**Packet ID:** TP-20261016-001  
**Status:** Complete  
**Created:** 2026-10-16  
**Last updated:** 2026-10-17
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261016-001-forecast-transaction-sign-contract.md`  
**Workstream size:** One targeted implementation packet  
**Priority:** P0  
**Depends on:** None  
**Series:** 11 packets (TP-20261016-001..011); assume each named prerequisite has landed before starting this packet.  

## Objective
Forecast Transaction Sign Contract and Reconciliation. Complete only the named workstream; no broad rediscovery.

## Do not rediscover: exact file/ownership map
- `backend/app/services/transaction_semantics.py (new)`
- `backend/app/services/forecast_v2_sources.py`
- `backend/app/routes/forecast.py`
- `backend/forecast/v2_sources.py`
- `backend/forecast/v2_validation.py`
- `backend/app/sql/manual_import_logic.py`
- `tests/test_transaction_semantics.py (new)`
- `tests/test_forecast_v2_adapters.py`
- `tests/test_forecast_route.py`
- `tests/test_forecast_v2_validation.py`

## Confirmed current seam (main at authoring 437bdd9cda1bd21d651e7c0ecd24c205d76b6ebc)
`plaid_sync._upsert_transaction()` persists the provider `amount` (+ debit/outflow, - credit/inflow); `load_v2_source_data()` currently forwards `t.amount` verbatim to `forecast.v2_sources._prepare()`, which explicitly expects + inflow/- outflow. `routes/forecast.py:_daily_transaction_aggregates()` and `_detect_auto_wage/_detect_auto_rent` (inspect existing exact names) also decide direction from raw sign. `Transaction` has `provider=manual|plaid` but no transaction_type DB column; old manually imported signs may be ambiguous. No direct transaction DB rewrite is safe.

## Required code edits, in order
1. Create `transaction_semantics.py` pure `canonical_account_delta(*, provider, raw_amount, account_type, manual_direction=None)->Decimal|None`: for provider `plaid`, `-Decimal(raw_amount)` for both cash and liability accounts (positive cash delta means deposit, positive liability-account delta means debt decrease); zero stays zero. For manual with explicit import debit/credit indicator use that indicator; for legacy already-signed manual rows follow documented importer convention only when verifiable, otherwise return `None` + `sign_unknown` warning. Reject NaN/Inf, retain cents as Decimal; keep provider raw data untouched. Return separate `liability_balance_effect` only in packet 006. Add concise per-provider table.
2. `backend/app/services/forecast_v2_sources.py:load_v2_source_data`: join Account already loaded, pass normalized `amount` to V2 input, retain `raw_amount`, `amount_semantics`, `account_bucket` and `source_provider` for audit; skip unknown sign from recurrence/residual with a warning/count, never assume expense. Preserve user filter/as-of/pending/transfer metadata. `build_user_v2_inputs` and `forecast_v2_service.compute_v2_forecast` surface counts/warnings.
3. `backend/app/routes/forecast.py:_daily_transaction_aggregates`: replace SQL comparisons `Transaction.amount>0` (wrong for Plaid) with owner- and account-scoped grouping of canonical deltas, exclude pending/internal and noncash or explicitly label account scope; preserve V1 response schema. Apply same sign contract in existing auto wage/rent sign tests, not just output labels.
4. `backend/forecast/v2_validation.py:_match_realized` and backtest source inputs: normalize realized transaction sign at the loader boundary, not a second blind negate, so event matching compares the same units. Make account-scope and no-lookahead explicit. Do not modify `transactions.amount`, raw Plaid payloads, or chart/transactions display conventions.

## Exact contracts and acceptance fixtures
- Fixtures: checking Plaid purchase raw +60=>cash -60; paycheck raw -1000=>+1000; credit-card purchase raw +90=>liability charge (cash not paid yet); payment to card raw -90=>liability owed decreases; manual known +income/-expense unchanged; unknown manual direction excluded and diagnosed.
- Reconciliation per as-of day: starting_cash + signed cash events = ending_cash exactly; when real snapshots exist, compare predicted changes to observed signed movements without charging card purchases twice.

## Validation commands
`pytest tests/test_transaction_semantics.py tests/test_forecast_v2_adapters.py tests/test_forecast_v2_sources.py tests/test_forecast_v2_validation.py tests/test_forecast_route.py -q`; compare V1/V2 account-aware end-of-day records. No migration for this packet.

## Non-goals
No rewriting all historical transactions; no new UI; no recurrence inference changes; don't treat credit card purchases as immediate bank withdrawals.

## Implementation/handoff
Read `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate only named symbols against latest main. Set In Progress in tracker before coding. Treat prerequisite packets as implemented, do not re-implement their features. Run focused tests then lint/build; commit only this workstream to main without force, mark Complete, move this packet to completed and update INDEX/TRACKER atomically. Report changed files, test output, fixture/behavior evidence, and deviations. If principal is not trusted, fail closed on new owner-scoped endpoints, not permissive fallback. Do not use Plaid Enrich/new billable APIs.

## Completion report (2026-10-17)

- Added `backend/app/services/transaction_semantics.py` (`normalize_amount`, `canonical_account_delta`, `account_bucket`) with the per-provider table; Plaid is `-raw`, manual needs an explicit direction, unknown/non-finite amounts return `None` with `sign_unknown` / `invalid_amount`.
- `load_v2_source_data` now forwards canonical `amount` plus `raw_amount`, `amount_semantics`, `account_bucket`, `source_provider`; unknown-sign rows are excluded and counted in `sign_summary`; saved recurring rule amounts use the same contract. `compute_v2_forecast` surfaces a `sign_unknown_excluded` warning.
- `routes/forecast.py`: `_load_historical_aggregates` groups canonical deltas per day (owner-scoped, cash + liability accounts, pending/internal/unknown excluded); auto wage/rent detection uses canonical deltas.
- `forecast/v2_validation.history_loaders`: documented canonical units, realized rows limited to the supplied accounts (no second negate, no look-ahead).
- Tests: new `tests/test_transaction_semantics.py` (23 cases covering every packet fixture); `tests/forecast_v2_world.py` and `tests/test_forecast_v2_adapters.py` fixtures converted to Plaid-signed rows. Focused set passes per file; other failures in the repo are pre-existing and identical on a clean baseline.
- Deviations: `tests/test_forecast_route.py` is skipped on main before and after (its module stubs fail to import), so route behavior is covered in `test_transaction_semantics.py` and `test_forecast_v2_api.py` instead.
