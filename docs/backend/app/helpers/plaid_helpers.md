## 📘 `plaid_helpers.py`
```markdown
# Plaid Integration Helpers

Wrapper functions around the Plaid SDK for common operations like fetching
accounts, transactions, holdings, and generating link tokens. Also includes a
helper to store transactions JSON and a deprecated category refresh call.

**Dependencies**: `plaid_api` models, `app.config.plaid_client`,
`app.sql.forecast_logic`, `app.models.Category`, `app.extensions.db`.
```

## Source audit capture

`get_transactions(..., audit_source=True)` records original payloads per actual response page, including available Plaid request IDs, within the caller’s transaction and source run context. Legacy account refresh enables this option. Empty non-final pages fail instead of looping indefinitely. See [Plaid source history](../services/plaid_audit.md).
