# Process Note: Domain Separation for External API & DB Logic

### Date: 2025-05-24

### Goal
Maintain clean architectural separation between routing, domain logic, and external service integration.

---

### Current Structure

| Layer   | Responsibility                             | Location        |
|---------|--------------------------------------------|-----------------|
| Routes  | Handle HTTP requests, call services        | `app/routes/`   |
| Services| Domain and DB orchestration logic          | `app/services/` |
| Helpers | External API clients and small utilities   | `app/helpers/`  |
This structure keeps concerns isolated and makes the codebase easier to test.
### Pending Cleanup
- Move direct Plaid/Teller API calls out of `sql/account_logic.py`.
- Expose `sync_plaid_transactions` at the helper layer.
- Ensure SQL layer only operates on transformed data.
- [] Update `sql/` layer to operate on transformed data only

### ðŸ™ƒ File to Save This Note:
`process/architecture_notes.md`