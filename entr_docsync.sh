#!/bin/bash

TARGET_WINDOW="Arch Linux Assistant - OpenGithubSDK Status Report - qutebrowser"
MESSAGE="✅ Docs updated for OpenGithubSDK"

find . -type f -name "*.py" | entr -r sh -c '
  python cli.py --mode goal --goal document_undocumented_files --args "{\"repo_name\": \"OpenGithubSDK\"}" && \
  ./notify_qute.sh "'"$TARGET_WINDOW"'" "'"$MESSAGE"'"
'
