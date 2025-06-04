# backend/app/routes Documentation

---

## 📘 `manual_io.py`

````markdown
# Manual IO Route

## Purpose

Provides an interface for manually entering, editing, or deleting financial transactions. Used to supplement imported data with custom entries (e.g., cash expenses, corrections).

## Key Endpoints

- `POST /manual`: Add a new manual transaction.
- `GET /manual`: Retrieve all manual entries.
- `PATCH /manual/<id>`: Update a specific manual transaction.
- `DELETE /manual/<id>`: Delete a manual entry.

## Inputs & Outputs

- **POST /manual**

  - **Input:**
    ```json
    {
      "amount": 34.2,
      "date": "2024-12-10",
      "description": "Lunch - Cash",
      "category": "Food",
      "account_id": "acct_001"
    }
    ```
  - **Output:** Newly created transaction object with `id`

- **GET /manual**

  - **Output:** Array of manual transaction objects

- **PATCH /manual/<id>**

  - **Input:** Partial update (e.g., new `description`, `amount`)
  - **Output:** Updated transaction object

- **DELETE /manual/<id>**
  - **Output:** `{ success: true }` if entry removed

## Internal Dependencies

- `models.Transaction`
- `services.manual_transaction_service`
- Validation & ID generation utilities

## Known Behaviors

- Stored distinctly from imported transactions
- Edits are fully auditable
- Automatic merging into charts/summary data

## Related Docs

- [`docs/frontend/pages/ManualEntryForm.md`](../../frontend/pages/ManualEntryForm.md)
- [`docs/dataflow/manual_data_handling.md`](../../dataflow/manual_data_handling.md)
````

---

Next: `plaid.py`?
