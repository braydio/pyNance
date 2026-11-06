# `dashboard_activity_status.py`

## Purpose

Build the dashboard greeting/status payload from visible account balances and recent transactions. Return deterministic guidance unless an optional local model server is explicitly configured.

## Key behaviors

- Loads visible accounts and recent non-internal transactions for a configurable date range (default: trailing 30 days).
- Always produces rule-based guidance without model network access when the dashboard LLM message setting is disabled or its server URL is blank.
- When enabled with an explicit local/private-network URL, sends compact JSON context to that server's chat-completions endpoint.
- Accepts an Ollama host, `/v1` base URL, or complete `/chat/completions` endpoint. Public internet destinations and HTTP redirects are rejected to prevent accidental hosted-model requests.
- Enforces a parseable response contract: `status_key` and a short `message`.
- Falls back to deterministic guidance on configuration or model server errors.

## Public API

- `generate_activity_status(start_date=None, end_date=None, user_id=None) -> dict`: returns `{ status_key, message, source }` where `source` is `llm` or `fallback`.

## Operational notes

- Optional installed model: `LOCAL_LLM_MODEL` (default `llama3.2`).
- Model timeout is 15 seconds; provider failures never block dashboard status.
- The route payload and database settings contract are unchanged; no migration is needed.
