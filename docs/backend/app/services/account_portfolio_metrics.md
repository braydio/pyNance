# `account_portfolio_metrics`

Canonical, display-safe per-account metrics derived from persisted provider data (TP-20261014-005).

- `classify_account_group(account)` -> `depository | investment | credit | loan | other`.
- `compute_account_metrics(account, now=None, stale_after=48h)` returns `signed_balance` (liabilities negative), `owed` (liabilities only, never negative), `credit_limit`, `utilization_pct` (cards with a positive limit only), `overlimit`, `available_credit` with `available_credit_source` (`provider` | `derived`), and `balance_status` (`fresh | stale | unknown`).

Unknowns stay `None`: a missing limit never becomes `0`, and derived headroom is labelled `derived` rather than issuer-reported availability. Checking-account provider limits are overdraft limits and are not stored as `credit_limit`.

Sign convention: ingestion stores liabilities with the provider sign (positive = owed); `finance_utils.normalize_account_balance` is the single read-side flip.
