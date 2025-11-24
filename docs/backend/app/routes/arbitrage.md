# Arbitrage Route (`arbitrage.py`)

## Purpose
Serve the latest R/S arbitrage signal produced by the Discord bot pipeline by reading the most recent snapshot from disk.

## Endpoints
- `GET /api/arbitrage/current` – Load and return the contents of `ARBITRAGE_FILE`.

## Inputs/Outputs
- **GET /api/arbitrage/current**
  - **Inputs:** None.
  - **Outputs:** Parsed JSON payload from the snapshot file or `{ "content": <raw text> }` when the file is plain text or missing structured JSON.

## Auth
- Intended for authenticated dashboard clients; subject to standard auth middleware.

## Dependencies
- `app.config.constants.ARBITRAGE_FILE` for the snapshot path.
- Standard library `json` and `os.path.exists` for file handling.

## Behaviors/Edge Cases
- Invalid JSON falls back to returning the raw file contents to aid debugging.
- Returns an empty `content` string when the file is absent.

## Sample Request/Response
```http
GET /api/arbitrage/current HTTP/1.1
```

```json
{ "content": "No arbitrage data available" }
```
