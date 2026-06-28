---
Owner: Backend Team
Last Updated: 2026-05-30
Status: Active
---

# rsa_monitor.py

## Purpose

Expose local RSAssistant and AutoRSA runtime status to the pyNance frontend.

## Endpoint

- `GET /api/rsa-monitor/status`

## Response

```json
{
  "status": "success",
  "data": {
    "overall_status": "ok",
    "components": [],
    "heartbeat": {},
    "logs": [],
    "orders": {},
    "holdings": {},
    "account_history": {}
  }
}
```

## Auth

No route-specific auth is applied. This endpoint is intended for the local pyNance deployment and only returns whitelisted summaries.

## Dependencies

- `app.services.rsa_monitor.build_rsa_monitor_status`

## Behaviors/Edge Cases

- Runtime file absence is represented in the payload as `missing` or `degraded`.
- Unexpected service failures return `500` with the standard `{status, message}` shape.
