#!/usr/bin/env bash
# dev-helper.sh - Watch backend directory and restart Flask server on changes.
#
# Starts the Flask development server located in the backend directory and
# restarts it whenever files within that directory change. Requires
# inotifywait (from inotify-tools).

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${REPO_DIR}/backend"

command -v inotifywait >/dev/null 2>&1 || {
  echo "inotifywait is required but not installed. Please install inotify-tools." >&2
  exit 1
}

export FLASK_APP=run.py
export FLASK_ENV=development

FLASK_PID=0

start_flask() {
  echo "Starting Flask server..."
  cd "${BACKEND_DIR}"
  flask run &
  FLASK_PID=$!
  cd "${REPO_DIR}"
}

stop_flask() {
  if [ "${FLASK_PID}" -ne 0 ] && kill -0 "${FLASK_PID}" 2>/dev/null; then
    echo "Stopping Flask server (PID: ${FLASK_PID})"
    kill "${FLASK_PID}"
    wait "${FLASK_PID}" || true
  fi
}

trap stop_flask EXIT

start_flask

while inotifywait -r -e modify,create,delete,move "${BACKEND_DIR}"; do
  echo "Backend changes detected. Restarting Flask server..."
  stop_flask
  start_flask
done
