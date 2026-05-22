---
Owner: Backend Team
Last Updated: 2026-05-21
Status: Active
---

# codex_exec Route

## Purpose

Expose an admin-only execution endpoint for constrained Codex tasks with strict input validation, command construction, and audit logging.

## Endpoint

- **POST** `/api/codex/exec`

## Request Schema

```json
{
  "task": "<required text>",
  "preset": "<optional id>"
}
```

### Request Validation Rules

- `task` must be a non-empty string after trimming.
- `task` length must be `<= 400` characters.
- `task` must only use approved characters (`A-Z`, `a-z`, `0-9`, spaces, and `_. , : @ / + -`).
- Shell metacharacters and raw command strings are rejected.
- The service always constructs the command as `codex exec <task>` using argument arrays; callers cannot supply direct raw command arguments.

## Authorization

- Requires `X-Admin-Token` request header that matches server environment variable `CODEX_EXEC_ADMIN_TOKEN`.
- Unauthorized requests return HTTP `403`.

## Execution and Safety Controls

- Uses subprocess invocation with argument arrays (no `shell=True`).
- Applies timeout (`15s`).
- Captures and truncates stdout/stderr to bounded output limits.
- Maps execution failures to explicit HTTP statuses:
  - `400`: invalid input payload/task.
  - `403`: failed admin authorization.
  - `500`: command returned non-zero exit code.
  - `503`: execution backend unavailable (`codex` executable missing).
  - `504`: command timeout.

## Audit Logging

- Emits structured log event with:
  - requester (`X-Requester` header or `unknown`)
  - UTC timestamp
  - SHA-256 hash of task
  - SHA-256 hash of preset (if provided)
  - final execution status
- Raw task content and secrets are not logged.

## Response Schema

### Success (`200`)

```json
{
  "status": "success",
  "stdout": "...",
  "stderr": "..."
}
```

### Failure (`4xx/5xx`)

```json
{
  "status": "error",
  "error": "human-readable reason",
  "stdout": "optional bounded output",
  "stderr": "optional bounded output"
}
```
