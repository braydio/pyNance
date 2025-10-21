# Fidelity Route

## Purpose

Provide a thin HTTP wrapper around the Fidelity scraping/integration service.
When registered, the blueprint exposes a single read-only endpoint that returns
investment account snapshots sourced from `FidelityService`.

## Key Endpoints

- `GET /fidelity/investments` – Instantiate `FidelityService` and return the
  result of `get_investment_accounts()` as JSON.

## Inputs & Outputs

- No query or body parameters are required.
- Responses return the list of investment account dictionaries produced by the
  service.

## Internal Dependencies

- `app.services.fidelity_service.FidelityService`

## Known Behaviors

- The route performs no caching; each request initializes a new service
  instance, delegating authentication and scraping to the service layer.
- Applications must register the blueprint (e.g., with `/api/fidelity`) for the
  endpoint to become reachable.
