#!/bin/bash

# === Config ===
WATCH_PATH="./app"
REPO_NAME="pyNance"
TARGET_WINDOW="Arch Linux Assistant - pyNance Status - qutebrowser"

# === Watch ===
find "$WATCH_PATH" -type f -name "*.py" | entr -n sh -c '
  FILE_CHANGED="$0"
  echo "Change detected in: $FILE_CHANGED"

  # Run documentation goal
  python cli.py --mode goal --goal document_undocumented_files --args "{\"repo_name\": \"'$REPO_NAME'\"}"

  # Extract filename for human-readable message
  FILENAME=$(basename "$FILE_CHANGED")
  MESSAGE=\"🔄 Docs refreshed for $FILENAME\"

  # Send update to qute window
  ./scripts/notify_qute.sh "'"$TARGET_WINDOW"'" "$MESSAGE"
'
