---
Owner: Backend Team
Last Updated: 2026-05-30
Status: Active
---

# rsa_monitor.py

## Purpose

Build read-only runtime summaries for the local RSAssistant and AutoRSA production directories.

## Inputs/Outputs

- **Inputs:** Fixed local paths, optionally overridden with `RSASSISTANT_ROOT` and `AUTORSA_GUI_ROOT`.
- **Outputs:** Component status, heartbeat freshness, recent log lines, queued/sent order counts, holdings aggregates, and latest AutoRSA account-history totals.

## Safety Notes

- The service does not accept path input from requests.
- Credential folders, `.env` files, screenshots, and raw account identifiers are not exposed.
- Recent log lines are redacted for common token, key, password, and bearer-token patterns.
- The service reads files only; it does not execute runtime commands or mutate Production data.

## Dependencies

- Python standard library only: `csv`, `json`, `pathlib`, and `datetime`.
- Default roots:
  - `~/Production/RSAssistant`
  - `~/Production/RSAssistant/AutoRSA-GUI.local`

## Behaviors/Edge Cases

- Missing runtime files return degraded component statuses instead of raising.
- Heartbeat is stale after 180 seconds.
- Log summaries inspect only the tail of each file to keep the endpoint bounded.
