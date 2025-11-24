---
Owner: Backend Team
Last Updated: 2025-11-24
Status: Active
---

# Dashboard Route (`dashboard.py`)

## Purpose
Serve dashboard configuration data including account snapshot selections and customizable account groups to power personalized views.

## Endpoints
- `GET /api/dashboard/account_snapshot` – Return the persisted snapshot selection and hydrated account metadata.
- `PUT /api/dashboard/account_snapshot` – Validate and persist account snapshot selections.
- `GET /api/dashboard/account-groups` – Load all account groups and the active preference.
- `POST /api/dashboard/account-groups` – Create and activate a new account group.
- `PUT /api/dashboard/account-groups/<group_id>` – Update group display metadata.
- `DELETE /api/dashboard/account-groups/<group_id>` – Remove a group and resequence remaining groups.
- `POST /api/dashboard/account-groups/reorder` – Persist a new group ordering.
- `PUT /api/dashboard/account-groups/active` – Set the active group preference.
- `POST /api/dashboard/account-groups/<group_id>/accounts` – Attach an account to a group.
- `DELETE /api/dashboard/account-groups/<group_id>/accounts/<account_id>` – Detach an account from a group.
- `POST /api/dashboard/account-groups/<group_id>/accounts/reorder` – Save the ordering of accounts within a group.

## Inputs/Outputs
- **Snapshot endpoints**
  - **Inputs:** Optional `user_id` in query/body for scoping.
  - **Outputs:** `{ "status": "success", "data": { ...snapshot payload... } }`.
- **Group endpoints**
  - **Inputs:** JSON bodies with identifiers (`group_id`, `group_ids`, `account_id`) and metadata to create, reorder, or update groups.
  - **Outputs:** Success payloads mirroring the request structure or updated group objects.

## Auth
- Requires authenticated context; selections are stored per user.

## Dependencies
- `app.services.account_snapshot` helpers (`build_snapshot_payload`, `update_snapshot_selection`).
- `app.services.account_groups` CRUD helpers for group and membership management.
- Application logger for defensive error logging.

## Behaviors/Edge Cases
- Falls back to default scope when no `user_id` is provided.
- Validation rejects missing or incorrectly typed payloads before delegating to services.
- Errors from the service layer are surfaced with `status: error` while logging the underlying exception.

## Sample Request/Response
```http
PUT /api/dashboard/account-groups/reorder HTTP/1.1
Content-Type: application/json

{ "group_ids": [1, 3, 2] }
```

```json
{ "status": "success", "data": { "group_ids": [1, 3, 2] } }
```
