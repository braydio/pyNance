# ⚙️ Teller Configuration

This page summarizes the environment variables and certificate files required to enable Teller integration.

## Environment Variables

- `TELLER_APP_ID` – application ID registered with Teller. Used by the frontend when launching the link flow and passed to backend routes for API requests.
- `TELLER_WEBHOOK_SECRET` – secret used to validate Teller webhook signatures. If not set, the webhook route is disabled.

These variables are loaded by `backend/app/config/environment.py` from your `.env` file.

## Certificate Placement

Teller requests are authenticated with mutual TLS certificates. Place your certificate files inside `backend/app/certs/`:

```
backend/app/certs/
  ├── certificate.pem
  └── private_key.pem
```

The sync logic and webhook routes reference these paths when making HTTPS requests to Teller.
