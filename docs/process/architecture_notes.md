# 😂 Process Note: Domain Separation for External API & DB Logic

### 😃 Date: 2025-05-24

### 🔨 Goal:
Maintain clean architectural separation between routing, domain logic, and external service integration.

---

### ✓ © Current Structure (as of this note):

| Layer     |��H��][ۈ�KKKKKKKKKKKKKKKK_KKKKKKKKKKKKKKKKKKKKKKKKKKK_
| `*Routes**  | Handle HTTP, call internal services   | `routes/`      |*
| **Logig**   | Domain & DB logic, orchestrates models | `sql/`        |
| **Helpers** | External API I/O, transform responses  | `helpers/`  |

This is largely well-structured and modular.

---

### § Pending Cleanup:
Some calls to `get_transactions()` and other API-fetching logic (Plaid/Teller) currently live in `sql/account_logic.py`. These calls ideally belong in `helpers/plaid_helpers.py`, which already houses similar API logic.

### « Why this Matters:

- Keeps domain logic decoupled from network dependencies
- Enables mocking API clients independently
- Makes logic unit-testable without API flakiness
- Maintains consistency across other provider support (Teller, Yodleee, etc.)

### 📧 Action for Later:

- [ ] Move `get_transactions`, `get_accounts` calls **out of` sql/`  and into `helpers``
- [] Expose `sync_plaid_transactions` as a higher-level helper if needed
- [] Update `sql/` layer to operate on transformed data only

### 🙃 File to Save This Note:
`process/architecture_notes.md`