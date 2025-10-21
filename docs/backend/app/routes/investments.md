# `investments.py`

Investment-specific APIs covering accounts, holdings, and transactions. Mounted
at `/api/investments`.

## Helpers & Dependencies

- `parse_transaction_filter_params` – validates optional filters and converts
  ISO date strings into `datetime.date` objects.
- `app.sql.investments_logic.get_investment_accounts` for the `/accounts` feed.
- `app.models.InvestmentHolding`, `InvestmentTransaction`, `Security` via
  SQLAlchemy queries.
- `app.extensions.db` for session access.

## Endpoints

| Method | Path                            | Description                                                                                                        |
| ------ | ------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `GET`  | `/api/investments/accounts`     | Returns Plaid-linked investment accounts using `investments_logic.get_investment_accounts`.                        |
| `GET`  | `/api/investments/holdings`     | Joins holdings with security metadata and returns enriched rows (quantity, cost basis, latest price).              |
| `GET`  | `/api/investments/transactions` | Provides paginated investment transactions filtered by optional account, security, type, subtype, start/end dates. |

## Pagination & Filtering

- Pagination is controlled by `page` (default `1`) and `page_size` (default `25`).
- Supported filters: `account_id`, `security_id`, `type`, `subtype`, `start_date`,
  `end_date`.
- Invalid date ranges raise `ValueError` and result in a 400 response with an
  error message.

## Response Shape

- `/transactions` returns `{ "status": "success", "data": { "transactions": [...], "total": <count>, "filters": {...} } }`.
- `/holdings` and `/accounts` wrap their payloads in `{ "status": "success", "data": ... }`.
