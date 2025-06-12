# Teller Certificates

This directory stores the TLS client credentials required to authenticate with the Teller API.

## Required files

- `certificate.pem` – your Teller client certificate
- `private_key.pem` – the private key paired with the certificate

## Generating or obtaining credentials

1. Log in to the [Teller dashboard](https://dashboard.teller.io/) and create a new certificate.
2. Download the `certificate.pem` and `private_key.pem` files provided by Teller (or use `teller certificates create` if you have the Teller CLI installed).
3. Copy both files into this folder.

## File permissions

The certificate and key should only be readable by the application user:

```bash
chmod 600 certificate.pem private_key.pem
```

Ensure the `certs` directory is not committed to version control.

## Rotation policy

Teller certificates have limited lifetimes. Generate and deploy a new pair regularly—at least every 90 days or as recommended by Teller. Replace the files here with the new versions and restart the backend.

