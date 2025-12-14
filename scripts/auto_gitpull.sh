#!/usr/bin/env bash
#
# Auto-pull helper that snapshots local changes before rebasing onto origin.
# - If the working tree is dirty, we create a local checkpoint commit so pulls
#   don't fail. The commit remains local (no auto-push).
# - After syncing, we refresh embeddings when `anythingllm` is available.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH="${BRANCH:-$(git -C "${REPO_DIR}" rev-parse --abbrev-ref HEAD)}"
CHECKPOINT_MSG_PREFIX="${AUTO_GITPULL_MESSAGE:-chore: autopull checkpoint}"
RUN_EMBED=${RUN_EMBED:-1}

cd "${REPO_DIR}"

create_checkpoint_commit() {
  if [[ -n "$(git status --porcelain)" ]]; then
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    git add -A
    git commit -m "${CHECKPOINT_MSG_PREFIX} (${timestamp})"
    echo "Created checkpoint commit to capture local changes."
  fi
}

safe_rebase() {
  git fetch origin "${BRANCH}"
  local local_sha remote_sha
  local_sha=$(git rev-parse "${BRANCH}")
  remote_sha=$(git rev-parse "origin/${BRANCH}")

  if [[ "${local_sha}" == "${remote_sha}" ]]; then
    echo "Branch '${BRANCH}' already up to date."
    return
  fi

  if ! git rebase "origin/${BRANCH}"; then
    echo "Rebase failed; aborting and leaving the worktree untouched."
    git rebase --abort || true
    exit 1
  fi
}

refresh_embeddings() {
  if [[ "${RUN_EMBED}" -eq 0 ]]; then
    return
  fi

  if command -v anythingllm >/dev/null 2>&1; then
    anythingllm embed ./backend || echo "Embedding backend failed; continuing."
    anythingllm embed ./frontend || echo "Embedding frontend failed; continuing."
  else
    echo "anythingllm not found; skipping embeddings."
  fi
}

create_checkpoint_commit
safe_rebase
refresh_embeddings

echo "Auto git pull complete."
