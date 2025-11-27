---
Owner: Backend Team
Last Updated: 2025-11-24
Status: Active
---

# Recurring Transactions Route (`recurring.py`)

## Purpose
Detect, configure, and track recurring transactions such as subscriptions, rent, or utilities to provide visibility into fixed obligations.

## Endpoints
- `GET /recurring` – Return detected recurring transactions.
- `POST /recurring/confirm` – Confirm a transaction pattern as recurring.
- `DELETE /recurring/<id>` – Remove or disable tracking of a recurring item.
- `POST /recurring/scan/<account_id>` – Scan an account and persist newly detected recurring entries.

## Inputs/Outputs
- **GET /recurring**
  - **Inputs:** None.
  - **Outputs:** Array of recurring entries with description, amount, frequency, and next expected date.
- **POST /recurring/confirm**
  - **Inputs:** `{ "transaction_id": "txn_812", "confirmed_label": "Spotify Subscription" }`.
  - **Outputs:** Updated recurring entry metadata.
- **DELETE /recurring/<id>**
  - **Inputs:** Path parameter `id`.
  - **Outputs:** `{ "success": true }` on successful disable.
- **POST /recurring/scan/<account_id>**
  - **Inputs:** Path parameter `account_id`.
  - **Outputs:** `{ "status": "success", "actions": [] }` summarizing detected changes.

## Auth
- Requires authenticated user; recurring items are scoped to the user's accounts.

## Dependencies
- `services.recurring_detector` for detection logic.
- `models.RecurringTransaction` and `models.Transaction` for storage.

## Behaviors/Edge Cases
- Recurrence inferred from merchant and cadence heuristics; user confirmation stabilizes predictions.
- Confirmed recurring entries feed budgeting and forecast views.

## Sample Request/Response
```http
POST /recurring/confirm HTTP/1.1
Content-Type: application/json

{ "transaction_id": "txn_812", "confirmed_label": "Spotify Subscription" }
```

```json
{ "id": "rec_001", "description": "Spotify Subscription", "amount": 9.99, "frequency": "monthly" }
```
