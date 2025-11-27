---
Owner: Backend Team
Last Updated: 2025-11-24
Status: Active
---

# Fidelity Route (`fidelity.py`)

## Purpose
Expose investment account snapshots by wrapping the Fidelity scraping/integration service behind a simple read-only endpoint.

## Endpoints
- `GET /fidelity/investments` – Instantiate `FidelityService` and return investment account data as JSON.

## Inputs/Outputs
- **GET /fidelity/investments**
  - **Inputs:** None.
  - **Outputs:** Array of investment account dictionaries returned by `get_investment_accounts()`.

## Auth
- Requires the standard authenticated session; upstream credentials are handled inside the service layer.

## Dependencies
- `app.services.fidelity_service.FidelityService` for scraping/authentication.
- Blueprint must be registered (commonly under `/api/fidelity`).

## Behaviors/Edge Cases
- No caching is performed; each request initializes a new service instance.
- Errors from upstream scraping bubble to the client for troubleshooting.

## Sample Request/Response
```http
GET /fidelity/investments HTTP/1.1
```

```json
[
  {
    "account_name": "Brokerage",
    "balance": 12500.55,
    "holdings": []
  }
]
```
