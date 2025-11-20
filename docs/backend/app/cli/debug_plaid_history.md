## 🛠️ `debug_plaid_history.py`

````markdown
# Debug Plaid Transaction History Coverage

Developer-focused CLI for proving that we've pulled every transaction Plaid
will return for a specific account. It walks backward in configurable windows,
deduplicates overlapping responses, and surfaces the earliest date Plaid
exposes.

**Location:** `backend/app/cli/debug_plaid_history.py`

## Usage

From the `backend/` directory (with `FLASK_APP=run.py`):

```bash
# Probe one account with 120-day windows and dump the unique txns to disk
flask debug-plaid-history --account <ACCOUNT_ID> --window-days 120 --output /tmp/plaid_history.json
```

Key options:
- `--start` / `--end`: constrain the date range (defaults: 2015-01-01 through today).
- `--window-days`: adjusts window size to avoid vendor-side truncation (default 180).
- `--output`: writes the deduplicated payload plus window metadata to JSON for inspection.

The command reports:
- Raw vs unique transaction counts and how many windows were used.
- The earliest and latest dates Plaid returned (helps validate history coverage).
- How many duplicate `transaction_id` rows were dropped and how many lacked IDs.
- Suggested guardrails for deduplicating pending/posted pairs.

## Deduplication Scaffold

- Treat Plaid `transaction_id` as the canonical key; allow updates when the amount,
  status, or metadata change instead of inserting a new row.
- When `transaction_id` is missing, fall back to a composite key of
  `(pending_transaction_id, date, amount, merchant_name)` to avoid inserting
  obvious duplicates while keeping distinct charges intact.
- Keep the transactions/sync cursor current per item to shrink overlapping pulls,
  then run periodic history probes with this CLI to verify earliest coverage.
- Prefer idempotent upserts at the database layer so historical replays do not
  corrupt existing data.
````
