Investments Implementation Roadmap (Updated)

Current State

- Backend
  - Models: `Security`, `InvestmentHolding`, `InvestmentTransaction` in place.
  - Upserts: holdings/securities via `upsert_investments_from_plaid`; transactions via `upsert_investment_transactions`.
  - Routes: link/exchange, `POST /api/plaid/investments/refresh`, `POST /api/plaid/investments/refresh_all`, and read endpoints under `/api/investments`.
  - Webhooks: `/api/webhooks/plaid` now handles `INVESTMENTS_TRANSACTIONS` and `HOLDINGS` events and triggers automatic refreshes.
  - Raw capture: full Plaid JSON stored in `securities.raw`, `investment_holdings.raw`, and `investment_transactions.raw`.

- Frontend
  - API helpers for list endpoints (transactions/holdings) and refresh.
  - Initial UI for holdings and investment transactions.

What’s Next (Prioritized)

1. Visibility & reliability
   - Add unit/integration tests for webhook refresh paths and upsert logic.
   - Add lightweight metrics/logs for counts and error rates.
2. Portfolio analytics
   - Allocation by account/institution/security; simple performance snapshots.
   - CSV export for investment transactions.
3. UX polish
   - Security detail drawer (price, identifiers, recent activity).
   - Filters: by security, type/subtype, date range.
4. Ops
   - Optional scheduled backfill job for historical transactions if needed.

Notes

- Raw JSON columns are for audit/rehydration; structured columns remain the query surface for UI performance.

Last updated: 2025-09-10
