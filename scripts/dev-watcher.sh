#!/usr/bin/env bash
# dev-watcher.sh - Run the frontend dev server and auto-pull repo updates.
#
# Starts `npm run dev` for the frontend and periodically checks the remote Git
# repository for updates. When new commits are detected on the tracked branch,
# the script pulls the changes (triggering any Git hooks) and restarts the dev
# server.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${REPO_DIR}/frontend"
BRANCH="${1:-$(git -C "${REPO_DIR}" rev-parse --abbrev-ref HEAD)}"
INTERVAL="${INTERVAL:-60}"

declare DEV_PID=0

start_dev() {
  echo "Starting npm dev server..."
  cd "${FRONTEND_DIR}"
  npm run dev &
  DEV_PID=$!
  cd "${REPO_DIR}"
}

stop_dev() {
  if [ "${DEV_PID}" -ne 0 ] && kill -0 "${DEV_PID}" 2>/dev/null; then
    echo "Stopping npm dev server (PID: ${DEV_PID})"
    kill "${DEV_PID}"
    wait "${DEV_PID}" || true
  fi
}

trap stop_dev EXIT

cd "${REPO_DIR}"
start_dev

while true; do
  git fetch origin "${BRANCH}"
  LOCAL=$(git rev-parse "${BRANCH}")
  REMOTE=$(git rev-parse "origin/${BRANCH}")
  if [ "${LOCAL}" != "${REMOTE}" ]; then
    echo "Changes detected on origin/${BRANCH}. Pulling updates..."
    stop_dev
    git pull --rebase
    start_dev
  fi
  sleep "${INTERVAL}"

done
