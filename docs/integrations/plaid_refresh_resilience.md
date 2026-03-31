---
Owner: Backend Team
Last Updated: 2026-03-23
Status: Active
---

## Plaid refresh resilience

- **Cooldowns:** When Plaid returns `ACCOUNTS_LIMIT` or `RATE_LIMIT_EXCEEDED`, the account enters a 10-minute cooldown. We skip refresh attempts during the cooldown to avoid wasting retries.
- **Status storage:** The last refresh status (success/error/code/request_id/cooldown_until/timestamp/version) is stored on `PlaidAccount.last_error` as JSON and updated on every refresh attempt. Successes overwrite older failures with a structured success payload; failures overwrite the prior payload with structured error details.
- **Staleness:** Refreshes older than 6 hours are treated as stale by default (configurable via the `sla_hours` query param).
- **Endpoints:**
  - `POST /api/accounts/refresh_accounts` now reports `rate_limited_skipped` in the payload.
  - `GET /api/accounts/refresh_status` returns per-account refresh status, cooldowns, and staleness flags for UI warnings.
- **Staggering:** Bulk refreshes are sorted by institution and staggered slightly between institutions to reduce burst load on Plaid.
- **Planned:** Add per-access-token cooldowns to further reduce rate-limit risk when multiple accounts share a token.

- **Investments parity:** `POST /api/plaid/investments/refresh`, `POST /api/plaid/investments/refresh_all`, and the Plaid `INVESTMENTS_TRANSACTIONS` / `HOLDINGS` webhook handlers now persist the same per-account refresh metadata that transaction refresh flows use.
- **Failure semantics:** Investment refresh failures are still returned or logged at the route/webhook layer, but they also persist structured account-level payloads so the UI and operators can distinguish generic errors from provider codes, request IDs, and rate-limit cooldowns.
- **Partial bulk behavior:** Bulk investments refreshes continue past per-item failures, but each affected account now records its own success or failure metadata instead of only contributing to aggregate logs.
