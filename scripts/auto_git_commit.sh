#!/bin/bash

# Usage: ./script.sh <filename> [-m "custom commit message"]

FILE=""
CUSTOM_MESSAGE=""

# Argument parsing
while [[ $# -gt 0 ]]; do
  case "$1" in
  -m | --message)
    CUSTOM_MESSAGE="$2"
    shift 2
    ;;
  *)
    if [[ -z "$FILE" ]]; then
      FILE="$1"
    else
      echo "Unexpected argument: $1"
      exit 1
    fi
    shift
    ;;
  esac
done

if [ -z "$FILE" ]; then
  echo "Usage: $0 <filename> [-m \"custom commit message\"]"
  exit 1
fi

if [ ! -f "$FILE" ]; then
  echo "File '$FILE' does not exist."
  exit 1
fi

# Run route linter before commit
scripts/lint_routes.py
STATUS=$?
if [ $STATUS -ne 0 ]; then
  echo "[LINTER] API route violations detected. Commit aborted."
  exit 1
fi

BASENAME=$(basename "$FILE")

# Fetch latest commit for the file
LATEST_COMMIT_MSG=$(git log -1 --pretty=%s -- "$FILE")

# Extract version number from commit message
if [[ $LATEST_COMMIT_MSG =~ ([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
  CURRENT_MAJOR=${BASH_REMATCH[1]}
  CURRENT_MINOR=${BASH_REMATCH[2]}
  CURRENT_PATCH=${BASH_REMATCH[3]}
  CURRENT_MINOR=$((CURRENT_MINOR + 1)) # Increment minor version
else
  CURRENT_MAJOR=1
  CURRENT_MINOR=0
  CURRENT_PATCH=0
fi

NEW_VERSION="$CURRENT_MAJOR.$CURRENT_MINOR.$CURRENT_PATCH"
DATE=$(date '+%Y-%m-%d')

# Compose commit message
if [ -n "$CUSTOM_MESSAGE" ]; then
  MESSAGE="$CUSTOM_MESSAGE - v$NEW_VERSION"
else
  MESSAGE="$DATE - $BASENAME - v$NEW_VERSION"
fi

git add "$FILE"
git commit -m "$MESSAGE"
git push

echo "Committed and pushed '$FILE' as version v$NEW_VERSION"
