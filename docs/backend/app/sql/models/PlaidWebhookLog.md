# 📘 `PlaidWebhookLog` Model

```markdown
# PlaidWebhookLog Model

## Purpose

Records incoming webhook payloads received from Plaid. Acts as an audit trail for external sync events, error tracking, and developer debugging.

## Fields

- `id`: Primary key (UUID)
- `event_type`: String — type of webhook (e.g., `TRANSACTIONS_REMOVED`, `SYNC_UPDATES_AVAILABLE`)
- `payload`: JSON blob of the full webhook body
- `status`: Enum or string (`received`, `processed`, `error`)
- `error_message`: Optional — populated if webhook failed processing
- `account_id`: FK to linked `Account`, if resolvable
- `user_id`: Optional FK — inferred from account linkage
- `created_at`: Timestamp of receipt
- `processed_at`: Nullable timestamp of processing

## Relationships

- Linked to `Account`, optionally to `User`

## Behaviors

- All webhooks stored before processing
- Failed payloads retained for manual retry/debug
- Noise-level webhooks may be throttled or collapsed

## Related Logic

- `plaid.py` route handler
- `sync_service.py`
- Error logging and retry queues

## Related Docs

- [`docs/sync/plaid_webhooks.md`](../../docs/sync/plaid_webhooks.md)
- [`docs/dev/debugging_sync_issues.md`](../../docs/dev/debugging_sync_issues.md)
```
