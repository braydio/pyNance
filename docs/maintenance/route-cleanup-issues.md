# Route Cleanup Notes

Generated: February 1, 2026

## Removed Stale Routes

- `backend/app/routes/plaid_transfer.py`
  - Standalone Flask app (`app = Flask(__name__)`) and `@app.route` handlers.
  - Blueprint defined but never registered in the app factory, so endpoints were unreachable.

- `backend/app/routes/product_transactions.py`
  - FastAPI `APIRouter` inside the Flask codebase.
  - Never registered anywhere in the Flask app factory.

- `backend/app/routes/plaid.py`
  - Blueprint registered at `/api/plaid`, but routes were `/plaid/link_token` and `/plaid/exchange_token`, resulting in `/api/plaid/plaid/...`.
  - Frontend uses `/api/plaid/transactions/*` and `/api/plaid/investments/*` endpoints instead.
  - Contains `json.jsdamp` typos, which would raise on call.

- Removed stale arbitrage blueprint registration from `backend/app/__init__.py`.

## Overlaps / Redundancy (Follow-up Required)

These endpoints overlap in functionality or data shape and should be reviewed before consolidation:

- Recurring endpoints:
  - `backend/app/routes/accounts.py` (`/api/accounts/<account_id>/recurring`, `/api/accounts/<account_id>/recurringTx`)
  - `backend/app/routes/recurring.py` (`/api/recurring/<account_id>/recurring`, `/api/recurring/accounts/<account_id>/recurringTx`)
  - Frontend uses both patterns; semantics differ slightly.

- Account transactions endpoints:
  - `backend/app/routes/transactions.py` (`/api/transactions/<account_id>/transactions`)
  - `backend/app/routes/accounts.py` (`/api/accounts/<account_id>/transaction_history`)
  - Similar intent, different response shapes and query behavior.

- Forecast endpoints:
  - `backend/app/routes/charts.py` (`/api/charts/forecast`)
  - `backend/app/routes/forecast.py` (`/api/forecast/compute`)
  - Frontend appears to use `/api/forecast/compute`; verify if `/api/charts/forecast` is still needed.

## Next Steps

- Decide whether to consolidate recurring and transaction endpoints with a compatibility layer.
- Confirm if `/api/charts/forecast` has any consumers before removal.
