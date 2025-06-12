# 🔧 Teller Configuration

This integration relies on a few environment variables and TLS certificates.

## Environment Variables

- `TELLER_APP_ID` – your Teller application ID used when initiating Teller Link.
- `TELLER_WEBHOOK_SECRET` – secret for verifying webhook signatures.

These are loaded in `app.config.environment` and typically defined in `backend/.env`.

## Certificates

Place your client certificate and private key in `backend/app/certs/`:

```
backend/app/certs/
  ├── certificate.pem
  └── private_key.pem
```

The sync logic and webhook routes reference these paths when making HTTPS requests to Teller.
