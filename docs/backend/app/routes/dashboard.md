# `dashboard.py`

API surface supporting the main account dashboard, including persisted snapshot
preferences and custom account groups.

## Blueprints & Dependencies

- Blueprint name: `dashboard`, registered under `/api/dashboard`.
- Relies on:
  - `app.services.account_snapshot.build_snapshot_payload` and
    `update_snapshot_selection` for snapshot hydration and persistence.
  - `app.services.account_groups` helpers for CRUD operations on custom
    account groupings.
  - `flask.request` query/body parameters for selecting the active user scope.

## Endpoints

### Account Snapshot

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET`  | `/api/dashboard/account_snapshot` | Returns the stored account selection and hydrates account balances via `build_snapshot_payload` (defaults to `DEFAULT_USER_SCOPE` when the user ID is omitted). |
| `PUT`  | `/api/dashboard/account_snapshot` | Validates a list of `selected_account_ids`, persists the preference with `update_snapshot_selection`, and returns the updated payload. |

Both endpoints accept an optional `user_id` query parameter or JSON field to
scope the preference record.

### Account Groups

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET` | `/api/dashboard/account-groups` | Returns all account groups for the requested user ID via `list_account_groups`. |
| `POST` | `/api/dashboard/account-groups` | Creates or upserts a group (`name`, `accent`, optional `id`) using `create_account_group`. |
| `PUT` | `/api/dashboard/account-groups/<group_id>` | Updates group metadata (`name`, `accent`). |
| `DELETE` | `/api/dashboard/account-groups/<group_id>` | Removes a group and returns the remaining groups. |
| `POST` | `/api/dashboard/account-groups/reorder` | Persists a new ordering for all groups using `reorder_account_groups`. |
| `PUT` | `/api/dashboard/account-groups/active` | Sets the active group identifier via `set_active_group`. |
| `POST` | `/api/dashboard/account-groups/<group_id>/accounts` | Adds an account to the group with `add_account_to_group`. |
| `DELETE` | `/api/dashboard/account-groups/<group_id>/accounts/<account_id>` | Removes the account using `remove_account_from_group`. |
| `POST` | `/api/dashboard/account-groups/<group_id>/accounts/reorder` | Saves ordering changes for accounts inside the group via `reorder_group_accounts`. |

All account-group endpoints accept the `user_id` scope in either the query
string or request body. Validation ensures the required identifiers are present
before calling into the service layer.

## Error Handling

- Service exceptions are logged with `app.config.logger` and surfaced as 500
  errors with a JSON error payload.
- Validation failures (missing IDs or list payloads) return a 400-level response
  with a descriptive error message.
