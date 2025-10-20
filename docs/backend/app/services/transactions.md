# backend/app/services Documentation

---

## 📘 `transactions.py`

```markdown
# Transactions Service

## Purpose

Provide a thin orchestration layer that delegates transaction synchronisation to
provider-specific adapters (currently Plaid). The service is intentionally
minimal while broader CRUD features live directly in the route layer.

## Key Responsibilities

- Accept provider hints from HTTP routes or background jobs.
- Dispatch to the appropriate provider module to perform syncs.
- Bubble unsupported providers as actionable errors for callers.

## Primary Functions

- `sync_transactions(provider: str, account_id: str)`
  - Routes the sync request to `app.providers.plaid.sync_transactions` when the
    provider is `"plaid"`.
  - Raises `ValueError` for unsupported providers so routes can surface a clear
    4xx response.

## Inputs

- `provider` identifier (e.g. `"plaid"`).
- `account_id` referencing the upstream account to synchronise.

## Outputs

- Whatever payload the provider adapter returns (typically status flags and
  change counts).
- Exceptions when the provider string is not recognised.

## Internal Dependencies

- `app.providers.plaid.sync_transactions`

## Related Docs

- [`docs/backend/app/routes/plaid_transactions.md`](../routes/plaid_transactions.md)
- [`docs/roadmaps/transactions.md`](../../roadmaps/transactions.md)
```

---

All service files now documented. Ready for summary, publishing, or moving to another layer?
