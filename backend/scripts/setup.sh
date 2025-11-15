#!/usr/bin/env bash
set -euo pipefail

# Simple dev bootstrap:
# - Ensure backend/.env exists (copied from example.env if missing)
# - Start Postgres via docker compose
# - Wait for DB readiness
# - Run migrations

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

BACKEND_ENV="${ROOT_DIR}/.env"
EXAMPLE_ENV="${ROOT_DIR}/example.env"

echo "==> pyNance backend setup starting"

if [[ ! -f "${BACKEND_ENV}" ]]; then
  if [[ -f "${EXAMPLE_ENV}" ]]; then
    echo "==> No backend .env found, copying from example.env"
    cp "${EXAMPLE_ENV}" "${BACKEND_ENV}"
    echo "    Edit ${BACKEND_ENV} to customize credentials as needed."
  else
    echo "ERROR: example.env not found; cannot bootstrap environment."
    exit 1
  fi
fi

if ! command -v docker &>/dev/null; then
  echo "ERROR: docker is required but not installed or not on PATH."
  exit 1
fi

if ! command -v docker compose &>/dev/null && ! command -v docker-compose &>/dev/null; then
  echo "ERROR: docker compose (v2) or docker-compose (v1) is required."
  exit 1
fi

DOCKER_COMPOSE_CMD="docker compose"
if ! command -v docker compose &>/dev/null && command -v docker-compose &>/dev/null; then
  DOCKER_COMPOSE_CMD="docker-compose"
fi

echo "==> Starting Postgres container (service: db)"
${DOCKER_COMPOSE_CMD} up -d db

echo "==> Waiting for Postgres to become ready..."
MAX_RETRIES=30
RETRY=0
until ${DOCKER_COMPOSE_CMD} exec db pg_isready -U user -d pynance >/dev/null 2>&1; do
  RETRY=$((RETRY + 1))
  if [[ "${RETRY}" -ge "${MAX_RETRIES}" ]]; then
    echo "ERROR: Postgres did not become ready in time."
    ${DOCKER_COMPOSE_CMD} logs db || true
    exit 1
  fi
  sleep 2
done
echo "==> Postgres is ready."

export FLASK_APP="run:app"

echo "==> Running database migrations (flask db upgrade)"
python -m flask db upgrade

echo "==> Backend setup complete. You can now run:"
echo "    python run.py"

