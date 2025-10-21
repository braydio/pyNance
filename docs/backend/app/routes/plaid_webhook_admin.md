# `plaid_webhook_admin.py`

Administrative utilities for managing Plaid webhook URLs. Mounted at
`/api/plaid/webhook`.

## Dependencies

- `plaid.model.item_webhook_update_request.ItemWebhookUpdateRequest`
- `app.config.plaid_client` – Plaid SDK client used to submit updates.
- `app.models.PlaidAccount` – resolves `item_id` values from local account IDs.
- `app.config.BACKEND_PUBLIC_URL` – default base for webhook URLs when none is provided.

## Endpoints

| Method | Path                            | Description                                                                                                                                                                 |
| ------ | ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `POST` | `/api/plaid/webhook/update`     | Accepts `item_id` or `account_id` plus optional `webhook_url`. Resolves the Plaid item, builds an `ItemWebhookUpdateRequest`, and calls `plaid_client.item_webhook_update`. |
| `POST` | `/api/plaid/webhook/update_all` | Bulk-updates the webhook URL for every known Plaid item. Returns arrays of updated item IDs and any errors encountered.                                                     |

## Behaviour Notes

- If the Plaid SDK version does not expose `ItemWebhookUpdateRequest`, the route
  returns a 500 error instructing the operator to upgrade.
- When a custom `webhook_url` is not supplied, the handler derives one from
  `BACKEND_PUBLIC_URL` and the standard `/api/webhooks/plaid` path.
- Input validation covers missing identifiers and failed account-to-item
  lookups, returning appropriate 4xx responses.
