#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

export FLASK_APP="run:app"

echo "==> Running dev seed (flask seed-dev)"
python -m flask seed-dev

