# Teller Certificates

This folder stores the TLS certificate and private key used to authenticate with the Teller API. The files are not committed to version control.

## Obtaining the files

1. Log into the Teller developer dashboard.
2. Download the client certificate (`certificate.pem`) and the matching private key (`private_key.pem`).
3. Copy both files into this directory.

You may also generate a new certificate/key pair from the dashboard if you need to rotate credentials.

## Permissions

Protect the credentials so only the application can read them:

```bash
chmod 600 certificate.pem private_key.pem
```

## Rotation

Teller recommends rotating client certificates periodically (for example every 90 days). When you issue a new pair, replace the files here and restart the backend service.
