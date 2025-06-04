# backend/app/routes Documentation

---

## 📘 `export.py`

````markdown
# Export Route

## Purpose

Provides functionality for users to export financial data for offline use or import into third-party tools. Formats include CSV and JSON. This route supports exporting transactions, accounts, and budget summaries.

## Key Endpoints

- `GET /export/transactions`: Download transactions as a CSV file.
- `GET /export/accounts`: Download account metadata in JSON.

## Inputs & Outputs

- **GET /export/transactions**

  - **Params (optional):**
    - `start_date`, `end_date` — to filter transactions
    - `format` (default: `csv`) — options: `csv`, `json`
  - **Output:** CSV or JSON file (content-disposition: attachment)

- **GET /export/accounts**
  - **Output:** JSON payload:
    ```json
    [
      {
        "id": "account_123",
        "institution": "Chase",
        "balance": 1532.44,
        "type": "checking"
      },
      ...
    ]
    ```

## Internal Dependencies

- `services.export_service`
- `utils.csv_writer`
- `models.Transaction`, `models.Account`

## Known Behaviors

- Automatically filters by authenticated user
- Uses streaming for large CSV files
- Proper MIME headers set for downloads
- Rate-limiting and pagination supported in backend

## Related Docs

- [`docs/frontend/pages/ExportPage.md`](../../frontend/pages/ExportPage.md)
- [`docs/dataflow/export_pipeline.md`](../../dataflow/export_pipeline.md)
````

---
