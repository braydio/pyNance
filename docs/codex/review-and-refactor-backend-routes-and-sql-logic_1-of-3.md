# Review and Refactor Backend Routes and SQL Logic

## Part 1

---

1. Open `backend/app/sql/account_logic.py`. Cut out the following functions (include all their helper functions such as `fetch_url_with_backoff`):

   - `fetch_url_with_backoff`
   - `refresh_data_for_teller_account`
   - `refresh_data_for_plaid_account`
   - `get_paginated_transactions`

2. Create full implementations of these functions in `backend/app/sql/transactions_logic.py`. Add necessary imports (`json`, `datetime`, `NamedTemporaryFile`, models, etc.) and a module-level docstring summarizing its role.
3. In `account_logic.py`, import these functions from `.transactions_logic` and expose them so that `account_logic.refresh_data_for_plaid_account` still works (temporary backward compatibility).
4. Update route modules that call these helpers to import from `app.sql.transactions_logic` instead:

   - `backend/app/routes/transactions.py`
   - `backend/app/routes/teller_transactions.py`
   - `backend/app/routes/teller_webhook.py`
   - `backend/app/routes/plaid_transactions.py`
   - `backend/app/routes/accounts.py`
   - `backend/app/routes/institutions.py`

5. Update any docstrings and inline comments in these routes to mention `transactions_logic` instead of `account_logic`.
6. Update tests that stub `account_logic` to instead stub `transactions_logic` (e.g., `tests/test_api_plaid_transactions.py`, `tests/test_api_teller_transactions.py`, `tests/test_api_teller_link.py`, `tests/test_api_institutions.py`).
7. Write a new documentation page in `docs/backend/app/sql/transactions_logic.md` describing the moved functions and update `docs/backend/app/sql/index.md` to reflect the module’s real contents

---

## PART 2

---

1. Edit `backend/app/routes/categories.py`:

   - Replace the manual loop inside `refresh_plaid_categories` with a call to `category_logic.upsert_categories_from_plaid_data(response.to_dict())`.
   - Remove the direct `db.session.commit()` if `category_logic` already commits.
   - Ensure `from app.sql import category_logic` is imported.

2. Update the route’s docstring (and any related comments) to mention `category_logic`.
3. Amend `docs/backend/app/routes/categories.md` to document that `/categories/refresh` delegates to `category_logic.upsert_categories_from_plaid_data`.
4. Add or adjust tests if present (none currently) to assert that the route calls `category_logic.upsert_categories_from_plaid_data`.

## PART 3

---

1. Populate `docs/backend/app/sql/transactions_logic.md` with a short overview of the module, listing functions moved from `account_logic`.
2. Ensure `docs/backend/app/sql/index.md` links to this file and describes which routes rely on it (transactions, teller_transactions, etc.).
3. Mention in `docs/backend/app/routes/index.md` that transaction routes now use `transactions_logic` for DB operations.
