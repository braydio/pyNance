# backend/app/routes Documentation

---

## 📘 `recurring.py`

````markdown
# Recurring Transactions Route

## Purpose

Handles detection, configuration, and tracking of recurring transactions such as subscriptions, rent, or utilities. Provides visibility into fixed financial obligations.

## Key Endpoints

- `GET /recurring`: Returns list of detected recurring transactions.
- `POST /recurring/confirm`: Confirms a transaction pattern as recurring.
- `DELETE /recurring/<id>`: Removes or disables tracking of a recurring item.

## Inputs & Outputs

- **GET /recurring**

  - **Output:**
    ```json
    [
      {
        "id": "rec_001",
        "description": "Spotify",
        "amount": 9.99,
        "frequency": "monthly",
        "next_date": "2024-12-01"
      }
    ]
    ```

- **POST /recurring/confirm**

  - **Input:**
    ```json
    {
      "transaction_id": "txn_812",
      "confirmed_label": "Spotify Subscription"
    }
    ```
  - **Output:** Updated recurring entry metadata

- **DELETE /recurring/<id>`**
  - **Output:** `{ success: true }` on successful disable

## Internal Dependencies

- `services.recurring_detector`
- `models.RecurringTransaction`, `models.Transaction`
- Pattern matching, frequency inference modules

## Known Behaviors

- Recurrence inferred from merchant + cadence heuristics
- User confirmation required before prediction affects forecasts
- Recurring entries appear in budget and forecast views

## Related Docs

- [`docs/dataflow/recurring_detection.md`](../../dataflow/recurring_detection.md)
- [`docs/models/RecurringTransaction.md`](../../models/RecurringTransaction.md)
````

---

Next: `teller.py`?
