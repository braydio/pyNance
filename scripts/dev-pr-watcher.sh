#!/usr/bin/env bash
# dev-pr-watcher.sh - Run the frontend dev server and auto-checkout updated PRs.
#
# Polls GitHub for open pull requests. When a new PR is opened or an existing PR
# receives new commits, the script fetches and checks out the most recently
# updated PR and restarts the dev server.
#
# Requires: curl, jq. Set GITHUB_TOKEN to increase GitHub API rate limits.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${REPO_DIR}/frontend"
INTERVAL="${INTERVAL:-60}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

REMOTE_URL=$(git -C "${REPO_DIR}" remote get-url origin 2>/dev/null || true)
if [ -z "${REMOTE_URL}" ]; then
  echo "No 'origin' remote configured; exiting." >&2
  exit 1
fi
OWNER_REPO=$(echo "${REMOTE_URL}" | sed -nE 's#.*github.com[:/](.*)/(.*)(\\.git)?#\1/\2#p')
OWNER="${OWNER_REPO%%/*}"
REPO="${OWNER_REPO##*/}"

LAST_PR_NUMBER=""
LAST_PR_UPDATED=""

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
    DEV_PID=0
  fi
}

fetch_latest_pr() {
  local api_url="https://api.github.com/repos/${OWNER}/${REPO}/pulls?state=open&sort=updated&direction=desc"
  local pr_data
  if [ -n "${GITHUB_TOKEN}" ]; then
    pr_data=$(curl -fsSL -H "Authorization: token ${GITHUB_TOKEN}" "${api_url}")
  else
    pr_data=$(curl -fsSL "${api_url}")
  fi
  LATEST_PR_NUMBER=$(echo "${pr_data}" | jq -r '.[0].number // empty')
  LATEST_PR_UPDATED=$(echo "${pr_data}" | jq -r '.[0].updated_at // empty')
}

checkout_latest_pr() {
  git -C "${REPO_DIR}" fetch origin "pull/${LATEST_PR_NUMBER}/head:pr-${LATEST_PR_NUMBER}"
  git -C "${REPO_DIR}" checkout "pr-${LATEST_PR_NUMBER}"
  LAST_PR_NUMBER="${LATEST_PR_NUMBER}"
  LAST_PR_UPDATED="${LATEST_PR_UPDATED}"
}

trap stop_dev EXIT

cd "${REPO_DIR}"
fetch_latest_pr
if [ -n "${LATEST_PR_NUMBER}" ]; then
  checkout_latest_pr
fi
start_dev

while true; do
  fetch_latest_pr
  if [ -n "${LATEST_PR_NUMBER}" ] && { [ "${LATEST_PR_NUMBER}" != "${LAST_PR_NUMBER}" ] || [ "${LATEST_PR_UPDATED}" != "${LAST_PR_UPDATED}" ]; }; then
    echo "PR #${LATEST_PR_NUMBER} updated (${LATEST_PR_UPDATED}); checking out."
    stop_dev
    checkout_latest_pr
    start_dev
  fi
  sleep "${INTERVAL}"

done
