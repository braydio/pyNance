# `dashboard_activity_status.py`

## Purpose

Build the dashboard greeting/status payload from account balances and recent transactions, then request one parseable suggestion from an LLM when configured.

## Key behaviors

- Loads visible accounts and recent non-internal transactions for a configurable date range (default: trailing 30 days).
- Sends compact JSON context to OpenAI Chat Completions when `OPENAI_API_KEY` is present.
- Enforces a strict parseable response contract:
  - `status_key` (stable machine-friendly key)
  - `message` (single user-facing actionable sentence)
- Falls back to deterministic local guidance when API credentials are missing or the provider call fails.

## Public API

- `generate_activity_status(start_date=None, end_date=None, user_id=None) -> dict`
  - Returns `{ status_key, message, source }` where `source` is `llm` or `fallback`.

## Operational notes

- Optional model override: `OPENAI_DASHBOARD_MODEL` (default `gpt-4.1-mini`).
- Provider timeout is short (15s) so dashboard rendering can recover quickly.
- Route consumers should treat the payload as best-effort and preserve existing fallback copy.
