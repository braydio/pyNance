# Docs Routes (`docs.py`)

## Purpose

Expose a lightweight, auto-generated view of registered Flask routes for quick discovery in browsers and automation.

## Endpoints

- `GET /api/docs` – Render an inline HTML table of grouped routes and their HTTP methods.
- `GET /api/docs.json` – Return the same grouped structure as JSON.

## Inputs/Outputs

- **GET /api/docs**
  - **Inputs:** None.
  - **Outputs:** HTML page grouping routes by their first path segment.
- **GET /api/docs.json**
  - **Inputs:** None.
  - **Outputs:** JSON object keyed by base path with arrays of `{ "rule": str, "methods": [str] }` entries.

## Auth

- Intended for development visibility; no authentication or rate limiting is applied by default.

## Dependencies

- `_collect_routes()` helper iterating `current_app.url_map` while filtering static and auto-generated routes.
- Inline `render_template_string` for the HTML view.

## Behaviors/Edge Cases

- Output varies based on which blueprints are registered (e.g., feature flags such as `ENABLE_ARBIT_DASHBOARD`).
- Excludes `HEAD`/`OPTIONS` methods and static assets to reduce noise.

## Sample Request/Response

```http
GET /api/docs.json HTTP/1.1
```

```json
{
  "/api": [
    { "rule": "/api/accounts", "methods": ["GET"] },
    { "rule": "/api/transactions", "methods": ["GET", "POST"] }
  ]
}
```
