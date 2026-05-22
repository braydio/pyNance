---
Owner: Backend Team
Last Updated: 2026-05-21
Status: Active
---

# codex_exec_service

## Purpose

Provide a constrained service layer for validating and executing Codex commands with strict safety and audit controls.

## Public API

- `validate_task(task)` validates task type, emptiness, size, and allowed character set.
- `ensure_admin_authorized(admin_token)` enforces admin-token based execution gate.
- `build_command(task)` constructs the only allowed command: `['codex', 'exec', task]`.
- `execute_task(task)` runs subprocess execution with timeout and bounded output.
- `log_exec_audit(...)` emits structured audit logs with hashes instead of raw task content.

## Safety Controls

- No shell interpolation (`shell=True` is never used).
- Input task characters are allowlisted.
- Runtime timeout and output length limits are enforced.
- Errors are normalized into explicit status buckets (`success`, `failed`, `timeout`, `execution_unavailable`).

## Audit Behavior

- Logs include requester, timestamp, task hash, preset hash, and status.
- Logs avoid raw task/preset values to limit secret leakage risk.
