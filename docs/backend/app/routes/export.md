---
Owner: Backend Team
Last Updated: 2025-11-24
Status: Active
---

# Export Route (`export.py`)

## Purpose
Enable exporting financial data for offline analysis or import into third-party tools with CSV and JSON formats.

## Endpoints
- `GET /export/transactions` – Download transactions as CSV or JSON.
- `GET /export/accounts` – Download account metadata as JSON.

## Inputs/Outputs
- **GET /export/transactions**
  - **Inputs:** Optional `start_date`, `end_date`, and `format` (`csv` default, supports `json`).
  - **Outputs:** Attachment response streaming transactions in the requested format.
- **GET /export/accounts**
  - **Inputs:** None.
  - **Outputs:** JSON array of account records with IDs, institution names, balances, and types.

## Auth
- Requires authenticated user; exports are scoped to the requesting account set.

## Dependencies
- `services.export_service` and CSV writer utilities.
- `models.Transaction` and `models.Account` for source data.

## Behaviors/Edge Cases
- Streams large CSV responses to avoid memory pressure.
- Sets proper `Content-Disposition` headers for downloads.
- Honors backend rate limits and pagination when configured.

## Sample Request/Response
```http
GET /export/transactions?start_date=2024-01-01&end_date=2024-01-31 HTTP/1.1
```

```json
[
  {
    "id": "txn_001",
    "date": "2024-01-05",
    "amount": -45.23,
    "description": "Groceries"
  }
]
```
