# Net Changes API

The `/api/accounts/<account_id>/net_changes` endpoint reports income and expense totals for an account.

## Logic Overview
- `account_logic.get_net_changes` aggregates transactions within an optional date range using SQL sum functions.
- The accounts route parses `start_date` and `end_date` query params and returns JSON `{income, expense, net}`.

## Potential Issues
- Missing transactions or incorrect date parsing can lead to inaccurate totals.
- This endpoint currently relies on `Transaction.amount` signs to determine income vs expense.
