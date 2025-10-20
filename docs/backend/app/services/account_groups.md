# `account_groups.py`

## Responsibility
- Provide CRUD and ordering logic for custom dashboard account groups.
- Enforce membership limits and keep preferences synchronized after structural changes.

## Key Functions
- [`list_account_groups(user_id)`](../../../../backend/app/services/account_groups.py): Returns serialized groups for the scope, ensuring a default group and active preference exist.
- [`create_account_group(name, user_id, accent, group_id)`](../../../../backend/app/services/account_groups.py): Persists a new group with sequential positioning and sets it active.
- [`update_account_group(group_id, user_id, name, accent)`](../../../../backend/app/services/account_groups.py): Applies metadata updates while preserving existing memberships.
- [`delete_account_group(group_id, user_id)`](../../../../backend/app/services/account_groups.py): Removes a group, resequences remaining entries, and refreshes the active preference.
- [`add_account_to_group(group_id, account_id, user_id)`](../../../../backend/app/services/account_groups.py): Validates membership constraints before attaching an account.
- [`reorder_group_accounts(group_id, account_ids, user_id)`](../../../../backend/app/services/account_groups.py): Updates membership positions to match the requested ordering.

## Dependencies & Collaborators
- SQLAlchemy models: `Account`, `AccountGroup`, `AccountGroupMembership`, `AccountGroupPreference`.
- Normalizes account balances for presentation through [`app.utils.finance_utils.normalize_account_balance`](../../../../backend/app/utils/finance_utils.py).
- Shares account serialization semantics with [`account_snapshot`](./account_snapshot.md), allowing consistent UI rendering.

## Usage Notes
- Scope resolution defaults to the shared `"default"` user context when no explicit identifier is supplied.
- Membership operations enforce `MAX_ACCOUNTS_PER_GROUP` (currently 5) and remove stale memberships if backing accounts are missing.
