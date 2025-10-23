# Net Changes API

The `/api/accounts/<account_id>/net_changes` endpoint reports income, expense,
and net balance movement for an account.

## Logic Overview

- `account_logic.get_net_change` looks up balances in `AccountHistory` for
  the provided `start_date` and `end_date`.
- The net change is computed as `end_balance - start_balance`.
- The route returns a standard envelope `{"status": "success", "data": {"income", "expense", "net"}}`.
- For backward compatibility, legacy fields `{account_id, net_change, period:{start,end}}` are still included at the top level.

## Potential Issues

- Missing `AccountHistory` snapshots for the requested dates previously raised an
  error; now the legacy `net_change` is computed from snapshots (when available)
  and the breakdown is computed from transactions in the date range. Ensure your
  data backfill jobs (balance history aggregation) are running for best results.
