#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "==> Running dev seed (flask --app 'app:create_app' seed-dev)"
flask --app 'app:create_app' seed-dev
