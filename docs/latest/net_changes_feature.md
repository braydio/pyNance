# Net Changes API

The `/api/accounts/<account_id>/net_changes` endpoint reports balance
movements for an account.

## Logic Overview
- `account_logic.get_net_change` looks up balances in `AccountHistory` for
  the provided `start_date` and `end_date`.
- The net change is computed as `end_balance - start_balance`.
- The route returns JSON `{account_id, net_change, period:{start,end}}`.

## Potential Issues
- Missing `AccountHistory` snapshots for the requested dates will raise an
  error.
