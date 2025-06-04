| **Logig**   | Domain & DB logic, orchestrates models | `db_logic/`        |

Some calls to `get_transactions()` and other API-fetching logic (Plaid/Teller) currently live in `db_logic/account_logic.py`. These calls ideally belong in `helpers/plaid_helpers.py`, which already houses similar API logic.

- [ ] Move `get_transactions`, `get_accounts` calls **out of` db_logic/`  and into `helpers``
- [] Update `db_logic/` layer to operate on transformed data only

---

### âœ“ Â© Current Structure (as of this note):

| Layer     |›ÛHØØ][ÛˆŸKKKKKKKKKKKKKKKK_KKKKKKKKKKKKKKKKKKKKKKKKKKK_
| `*Routes**  | Handle HTTP, call internal services   | `routes/`      |*
| **Logig**   | Domain & DB logic, orchestrates models | `sql/`        |
| **Helpers** | External API I/O, transform responses  | `helpers/`  |

This is largely well-structured and modular.

---

### Â§ Pending Cleanup:
Some calls to `get_transactions()` and other API-fetching logic (Plaid/Teller) currently live in `sql/account_logic.py`. These calls ideally belong in `helpers/plaid_helpers.py`, which already houses similar API logic.

### Â« Why this Matters:

- Keeps domain logic decoupled from network dependencies
- Enables mocking API clients independently
- Makes logic unit-testable without API flakiness
- Maintains consistency across other provider support (Teller, Yodleee, etc.)

### ðŸ“§ Action for Later:

- [ ] Move `get_transactions`, `get_accounts` calls **out of` sql/`  and into `helpers``
- [] Expose `sync_plaid_transactions` as a higher-level helper if needed
- [] Update `sql/` layer to operate on transformed data only

### ðŸ™ƒ File to Save This Note:
`process/architecture_notes.md`