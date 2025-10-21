# Dashboard Route

## Purpose

Manages the data needed to render the personalized dashboard experience. The
blueprint exposes endpoints for retrieving and updating account snapshot
preferences as well as a full CRUD surface for user-defined account groups.
Logic heavy lifting is delegated to `app.services.account_snapshot` and
`app.services.account_groups`.

## Key Endpoints

- `GET /api/dashboard/account_snapshot` – Return the persisted snapshot
  selection together with hydrated account metadata via
  `build_snapshot_payload`.
- `PUT /api/dashboard/account_snapshot` – Validate and persist a list of
  account IDs by forwarding to `update_snapshot_selection`.
- `GET /api/dashboard/account-groups` – Load all account groups plus the active
  group preference through `list_account_groups`.
- `POST /api/dashboard/account-groups` – Create a group and activate it using
  `create_account_group`.
- `PUT /api/dashboard/account-groups/<group_id>` – Update group display
  metadata.
- `DELETE /api/dashboard/account-groups/<group_id>` – Remove a group and
  resequence remaining groups.
- `POST /api/dashboard/account-groups/reorder` – Persist a new group ordering.
- `PUT /api/dashboard/account-groups/active` – Set the active group preference.
- `POST /api/dashboard/account-groups/<group_id>/accounts` – Attach an account
  to a group.
- `DELETE /api/dashboard/account-groups/<group_id>/accounts/<account_id>` –
  Detach an account from a group.
- `POST /api/dashboard/account-groups/<group_id>/accounts/reorder` – Save the
  ordering of accounts within a group.

## Inputs & Outputs

- Snapshot endpoints accept an optional `user_id` in the query string or request
  body. Responses wrap payloads with `{ "status": "success", "data": ... }`
  or include error messaging when validation fails.
- Account group mutating endpoints expect JSON bodies that include identifiers
  such as `group_ids`, `group_id`, or `account_id` depending on the action.

## Internal Dependencies

- `app.services.account_snapshot.build_snapshot_payload`
- `app.services.account_snapshot.update_snapshot_selection`
- `app.services.account_groups` CRUD helpers for groups and memberships
- `app.config.logger` for defensive error logging

## Known Behaviors

- When no `user_id` is provided the routes fall back to the default scope.
- Validation rejects missing or incorrectly typed selection payloads before
  delegating to the services.
- Errors from the service layer are surfaced with `status: error` while still
  logging the underlying exception.
