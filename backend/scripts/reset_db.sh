#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

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

echo "==> Ensuring Postgres container (db) is running"
${DOCKER_COMPOSE_CMD} up -d db

echo "==> Dropping and recreating dev database 'pynance'"
${DOCKER_COMPOSE_CMD} exec -T db psql -U user -d postgres -c "DROP DATABASE IF EXISTS pynance;"
${DOCKER_COMPOSE_CMD} exec -T db psql -U user -d postgres -c "CREATE DATABASE pynance;"

echo "==> Running migrations after reset"
flask --app backend.run db upgrade

echo "==> Seeding demo data"
flask --app backend.run seed-dev

echo "==> Database reset and seed complete."

