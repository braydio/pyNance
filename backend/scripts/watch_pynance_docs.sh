#!/bin/bash

set -euo pipefail

# Shell wrapper to keep backward compatibility with historical workflows.
# Runs the repository-wide documentation coverage check. Defaults to the staged
# diff so the command can be used as a drop-in validation step in local scripts
# or CI jobs.

if command -v git >/dev/null 2>&1; then
  REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
else
  REPO_ROOT=""
fi

if [ -z "${REPO_ROOT}" ]; then
  SCRIPT_DIR=$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
  REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
fi

CHECK_SCRIPT="$REPO_ROOT/scripts/check_docs.py"

if [ ! -f "$CHECK_SCRIPT" ]; then
  echo "[DOCS] Unable to locate $CHECK_SCRIPT" >&2
  exit 1
fi

if [ $# -eq 0 ]; then
  set -- --staged
fi

python3 "$CHECK_SCRIPT" "$@"
