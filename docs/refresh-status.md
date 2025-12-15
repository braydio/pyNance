## Plaid refresh resilience

- **Cooldowns:** When Plaid returns `ACCOUNTS_LIMIT` or `RATE_LIMIT_EXCEEDED`, the account enters a 10-minute cooldown. We skip refresh attempts during the cooldown to avoid wasting retries.
- **Status storage:** The last refresh status (success/error/code/request_id/cooldown_until) is stored on `PlaidAccount.last_error` as JSON and updated on every refresh attempt.
- **Staleness:** Refreshes older than 6 hours are treated as stale by default (configurable via the `sla_hours` query param).
- **Endpoints:**
  - `POST /api/accounts/refresh_accounts` now reports `rate_limited_skipped` in the payload.
  - `GET /api/accounts/refresh_status` returns per-account refresh status, cooldowns, and staleness flags for UI warnings.
- **Staggering:** Bulk refreshes are sorted by institution and staggered slightly between institutions to reduce burst load on Plaid.

