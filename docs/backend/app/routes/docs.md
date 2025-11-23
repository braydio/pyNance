# Docs Route (`docs.py`)

API documentation blueprint that surfaces the current Flask `url_map` in both HTML and JSON forms for quick discovery.

## Purpose

- Expose a lightweight HTML page at `/api/docs` summarizing all registered routes, grouped by first path segment.
- Provide a machine-readable listing at `/api/docs.json` for tooling or API clients.
- Filter out noise by skipping static assets plus `HEAD`/`OPTIONS` auto-routes.

## Endpoints

- `GET /api/docs` — renders a minimal, inline-styled HTML view of grouped routes and their HTTP methods.
- `GET /api/docs.json` — returns the same grouped structure as JSON.

## How It Works

- Uses `_collect_routes()` to iterate `current_app.url_map`, drop static/auto routes, and group by leading path segment.
- HTML template is defined inline (`render_template_string`) to avoid separate asset management.
- Registered in `create_app()` with `url_prefix="/api/docs"` so the effective paths are `/api/docs` and `/api/docs.json`.

## JSON Shape

```json
{
  "/api": [
    { "rule": "/api/accounts", "methods": ["GET"] },
    { "rule": "/api/transactions", "methods": ["GET", "POST"] }
  ],
  "/api/plaid": [
    { "rule": "/api/plaid/link", "methods": ["POST"] }
  ]
}
```

## Notes and Limitations

- Intended for development/debug visibility; no authentication or rate limiting is applied here.
- Output depends on which blueprints are registered in the current app context and will vary by environment flags.
