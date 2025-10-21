# 📘 `PlaidWebhookLog` Model

```markdown
# PlaidWebhookLog Model

## Purpose

Captures every inbound webhook delivered by Plaid so operators can audit sync
activity, replay payloads during incident response, and diagnose processing
failures.

## Fields

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer (PK) | Auto-incrementing identifier. |
| `event_type` | String(128) | Convenience label built from `webhook_type:webhook_code`. |
| `webhook_type` | String(64) | Plaid webhook type (e.g., `TRANSACTIONS`). |
| `webhook_code` | String(64) | Plaid webhook code (e.g., `SYNC_UPDATES_AVAILABLE`). |
| `item_id` | String(128) | Plaid item identifier used to locate linked accounts. |
| `payload` | JSON | Raw request body stored for debugging and reprocessing. |
| `received_at` | DateTime | Naive UTC timestamp captured on receipt. |
| `created_at` | DateTime | Timestamp from `TimestampMixin`; set automatically. |
| `updated_at` | DateTime | Timestamp from `TimestampMixin`; refreshed on updates. |

## Relationships

- None. The table is an append-only log without foreign keys.

## Behaviors

- The Plaid webhook route logs every accepted payload via
  [`plaid_webhook.handle_plaid_webhook`](../../../../../backend/app/routes/plaid_webhook.py)
  before dispatching sync work, guaranteeing an audit trail even when downstream
  processing fails.
- Timestamps are stored without timezone awareness to mirror database defaults,
  matching the behavior enforced by `TimestampMixin`.

## Related Logic

- [`institution_models.py`](../../../../../backend/app/models/institution_models.py)
- [`plaid_webhook.py`](../../../../../backend/app/routes/plaid_webhook.py)

## Related Docs

- [`plaid_webhook.md`](../../routes/plaid_webhook.md)
- [`plaid_sync.md`](../../services/plaid_sync.md)
```
