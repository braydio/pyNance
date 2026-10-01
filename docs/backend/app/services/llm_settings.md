# LLM Settings Service

## Purpose

Persist and validate application-wide configuration for the optional LLM-generated dashboard message.

## Behavior

- Creates a singleton settings row on first use with custom messages enabled and no custom URL.
- Accepts blank URLs to select OpenAI, or HTTP(S) URLs for OpenAI-compatible providers such as Ollama.
- Rejects malformed URLs and URLs containing embedded credentials.
- Exposes API-safe payloads containing only `custom_message_enabled` and `base_url`.

The API key and model remain environment configuration. Custom endpoints default to the Ollama model `llama3.2`; set `OPENAI_DASHBOARD_MODEL` to choose another installed model.
