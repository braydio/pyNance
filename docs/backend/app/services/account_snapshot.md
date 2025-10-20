# `account_snapshot.py`

## Responsibility
- Manage the dashboard "snapshot" selection that highlights prioritized asset and liability accounts.
- Normalize persisted selections when underlying accounts change visibility or existence.

## Key Functions
- [`build_snapshot_payload(user_id)`](../../../../backend/app/services/account_snapshot.py): Loads visible accounts, ensures a preference row exists, normalizes stored selections, and returns the dashboard payload.
- [`update_snapshot_selection(selected_account_ids, user_id)`](../../../../backend/app/services/account_snapshot.py): Persists a curated selection after validating IDs against current accounts and enforcing maximum counts.

## Supporting Helpers
- Default selection logic via `_default_snapshot_ids` emphasizes the largest assets and liabilities using [`normalize_account_balance`](../../../../backend/app/utils/finance_utils.py).
- `_build_payload` serializes accounts, augmenting them with Plaid refresh metadata when available through the `Account.plaid_account` relationship.

## Dependencies & Collaborators
- SQLAlchemy models: `Account`, `AccountSnapshotPreference`.
- Works with account grouping preferences in [`account_groups`](./account_groups.md) to present curated dashboards.

## Usage Notes
- Snapshot scope defaults to the shared `"default"` user scope but can be overridden per user.
- Invalid or stale account IDs are automatically pruned and recorded in the payload metadata.
