# `arbitrage.py`

Provides read-only access to the most recent arbitrage snapshot produced by the Discord bot.

## Endpoints

- `GET /api/arbitrage/current` – Reads `app.config.constants.ARBITRAGE_FILE`. If the file contains valid JSON the payload is
  proxied as-is; otherwise the raw file contents are returned under a `content` key.

## Behaviour & Dependencies

- Uses `app.config.constants.ARBITRAGE_FILE` to locate the shared export written by background automation.
- Falls back to an empty `content` string if the snapshot file is missing.
- Does not persist any data; the endpoint is a thin façade over the exported snapshot file.

## Related Modules

- Discord arbitrage bot responsible for writing the snapshot file.
- [`docs/backend/app/routes/arbit_dashboard.md`](arbit_dashboard.md) – higher level dashboard data sources that can consume the
  same snapshot information.
