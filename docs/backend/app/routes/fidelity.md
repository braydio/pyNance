# `fidelity.py`

Thin wrapper around `app.services.fidelity_service.FidelityService` for
retrieving brokerage account information. The blueprint is declared as
`Blueprint("fidelity", __name__)`; when mounted without an additional prefix the
route resolves to `/fidelity/investments`.

## Dependencies

- `app.services.fidelity_service.FidelityService`
  - Expected to encapsulate authentication and scraping/API calls to Fidelity.

## Endpoint

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET` | `/fidelity/investments` | Instantiates `FidelityService` and returns the JSON representation of investment accounts. |

## Notes

- The response mirrors whatever structure `FidelityService.get_investment_accounts`
  returns (typically a list of account dictionaries).
- There is no request body or query parameter handling; authentication details
  are delegated entirely to the service implementation.
