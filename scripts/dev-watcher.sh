#!/usr/bin/env bash
# dev-watcher.sh - Run the frontend dev server and auto-pull repo updates.
#
# Starts `npm run dev` for the frontend and periodically checks the remote Git
# repository for updates. When new commits are detected on the tracked branch,
# the script checkpoints local changes, rebases onto the remote branch, runs
# formatters/lint hooks, and restarts the dev server. Hook failures are reported
# but do not kill the watcher.

set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${REPO_DIR}/frontend"
BRANCH="${1:-$(git -C "${REPO_DIR}" rev-parse --abbrev-ref HEAD)}"
INTERVAL="${INTERVAL:-360}"
CHECKPOINT_MSG_PREFIX="${AUTO_GITPULL_MESSAGE:-chore: dev-watcher checkpoint}"
HOOK_FIX_MSG_PREFIX="${AUTO_GITPULL_HOOK_MESSAGE:-chore: dev-watcher hook fixes}"
RUN_FRONTEND_FORMAT="${RUN_FRONTEND_FORMAT:-1}"
RUN_FRONTEND_LINT="${RUN_FRONTEND_LINT:-1}"
RUN_PRE_COMMIT="${RUN_PRE_COMMIT:-1}"

declare DEV_PID=0

log() {
  printf '[dev-watcher] %s\n' "$*"
}

start_dev() {
  if [ "${DEV_PID}" -ne 0 ] && kill -0 "${DEV_PID}" 2>/dev/null; then
    return 0
  fi

  log "Starting npm dev server..."
  (cd "${FRONTEND_DIR}" && npm run dev) &
  DEV_PID=$!
}

stop_dev() {
  if [ "${DEV_PID}" -ne 0 ] && kill -0 "${DEV_PID}" 2>/dev/null; then
    log "Stopping npm dev server (PID: ${DEV_PID})"
    kill "${DEV_PID}"
    wait "${DEV_PID}" || true
  fi
  DEV_PID=0
}

restart_dev() {
  stop_dev
  start_dev
}

ensure_dev_running() {
  if [ "${DEV_PID}" -eq 0 ] || ! kill -0 "${DEV_PID}" 2>/dev/null; then
    log "Dev server is not running; starting it again."
    DEV_PID=0
    start_dev
  fi
}

trap stop_dev EXIT

checkpoint_local_changes() {
  if [[ -n "$(git status --porcelain)" ]]; then
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    git add -A
    if git diff --cached --quiet; then
      return 0
    fi
    if git commit -m "${CHECKPOINT_MSG_PREFIX} (${timestamp})"; then
      log "Saved local changes to checkpoint commit before pulling."
    else
      log "Checkpoint commit failed; leaving changes in place and skipping pull."
      return 1
    fi
  fi
}

rebase_onto_remote() {
  if ! git rebase "origin/${BRANCH}"; then
    log "Rebase failed; aborting to preserve the worktree."
    git rebase --abort || true
    return 1
  fi
  return 0
}

run_command_nonfatal() {
  local description="$1"
  shift

  log "${description}..."
  if "$@"; then
    log "${description} completed."
    return 0
  fi

  local status=$?
  log "${description} failed with exit ${status}; watcher will continue."
  return "${status}"
}

run_pre_commit_hooks() {
  if [ "${RUN_PRE_COMMIT}" != "1" ]; then
    log "Skipping pre-commit hooks because RUN_PRE_COMMIT=${RUN_PRE_COMMIT}."
    return 0
  fi
  if ! command -v pre-commit >/dev/null 2>&1; then
    log "pre-commit is not installed; skipping backend formatter/lint hooks."
    return 0
  fi

  local before after
  before="$(git status --porcelain)"
  run_command_nonfatal "Running pre-commit hooks" pre-commit run --all-files
  after="$(git status --porcelain)"

  if [ "${before}" != "${after}" ]; then
    log "Pre-commit modified files; rerunning hooks once against formatter output."
    run_command_nonfatal "Rerunning pre-commit hooks" pre-commit run --all-files
  fi
}

run_frontend_format_and_lint() {
  if [ ! -f "${FRONTEND_DIR}/package.json" ]; then
    return 0
  fi
  if ! command -v npm >/dev/null 2>&1; then
    log "npm is not installed; skipping frontend format/lint."
    return 0
  fi

  if [ "${RUN_FRONTEND_FORMAT}" = "1" ]; then
    run_command_nonfatal "Running frontend formatter" npm --prefix "${FRONTEND_DIR}" run format
  fi
  if [ "${RUN_FRONTEND_LINT}" = "1" ]; then
    run_command_nonfatal "Running frontend lint" npm --prefix "${FRONTEND_DIR}" run lint
  fi
}

checkpoint_hook_changes() {
  if [[ -z "$(git status --porcelain)" ]]; then
    return 0
  fi

  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  git add -A
  if git diff --cached --quiet; then
    return 0
  fi

  if git commit -m "${HOOK_FIX_MSG_PREFIX} (${timestamp})"; then
    log "Saved formatter/lint hook changes to checkpoint commit."
  else
    log "Could not commit formatter/lint hook changes; leaving them in the worktree."
    return 1
  fi
}

run_post_update_hooks() {
  run_pre_commit_hooks
  run_frontend_format_and_lint
  checkpoint_hook_changes || true
}

check_for_updates() {
  if ! git fetch origin "${BRANCH}"; then
    log "Fetch failed for origin/${BRANCH}; retrying later."
    return 1
  fi

  local local_ref remote_ref
  local_ref=$(git rev-parse "${BRANCH}") || return 1
  remote_ref=$(git rev-parse "origin/${BRANCH}") || return 1

  if [ "${local_ref}" = "${remote_ref}" ]; then
    return 0
  fi

  log "Changes detected on origin/${BRANCH}. Pulling updates..."
  if ! checkpoint_local_changes; then
    return 1
  fi

  if rebase_onto_remote; then
    run_post_update_hooks
    restart_dev
  else
    log "Pull failed; keeping dev server alive with existing code."
  fi
}

cd "${REPO_DIR}"
start_dev

while true; do
  ensure_dev_running
  check_for_updates || true
  sleep "${INTERVAL}"
done
