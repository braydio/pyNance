# LLM Settings Service

## Purpose

Persist and validate application-wide configuration for optional local-model dashboard messages.

## Behavior

- Creates a singleton settings row on first use, with a custom-message toggle and no server URL.
- A blank URL means deterministic dashboard messages with **no model request**, even when the toggle is enabled.
- Accepts explicit HTTP(S) model server URLs on localhost or a private/non-global network, including a local Ollama service.
- Rejects public internet destinations, malformed URLs, URL-embedded credentials, query strings, and fragments.
- Revalidates persisted settings at the point of sending a model request, so older configurations fail closed.
- Exposes API-safe payloads containing only `custom_message_enabled` and `base_url`.

Local endpoints default to the installed model `llama3.2`; set `LOCAL_LLM_MODEL` to choose another locally installed model. There is no hosted-model API key configuration.
