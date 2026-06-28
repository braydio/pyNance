#!/bin/sh
# pyNance Docker entrypoint
#
# Runs database migrations on startup, then hands off to gunicorn.
# Fail fast on any error.
set -e

APP_DIR="/app/backend"

echo "==> pyNance backend — working directory: ${APP_DIR}"
cd "${APP_DIR}"

# ── Database migrations ──────────────────────────────────────────
echo "==> Applying any pending Alembic migrations..."
flask --app 'app:create_app' db upgrade
echo "==> Migrations complete."

# ── Start gunicorn ───────────────────────────────────────────────
echo "==> Starting gunicorn (workers=4)..."
exec gunicorn wsgi:app \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
