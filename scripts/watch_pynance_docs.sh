#!/usr/bin/env bash

# === CONFIGURATION ===
SDK_PATH="/home/braydenchaffee/Projects/OpenAII/OpenGithubSDK/cli.py"
REPO_NAME="pyNance"
WATCH_DIR="backend/app"
QUTE_WINDOW="Arch Linux Assistant - pyNance Status - qutebrowser"

# === WATCH ===
find "$WATCH_DIR" -type f -name "*.py" | entr -n sh -c '
  FILE_CHANGED="$0"
  echo "🐈 Change detected in: $FILE_CHANGED"

  # Trigger doc goal
  python3 "$SDK_PATH" \\
    --mode goal \\
      --goal document_undocumented_files \\
      --args {{\"repo_name\": "PyNance"}}

  # Notify Qute browser
  FILENAME=$(basename "$FILE_CHANGED"))
  MESSAGE="\u20B2\u3F9 Updated documentation for $FILENAME"

  /home/braydenchaffee/Projects/OpenAII/OpenGithuSDK/scripts/notify_qute.sh "$QUTE_WINDOW" "$MESSAGE"
