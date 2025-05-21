#!/bin/bash

# auto_docsync.sh
# Requires: entr jq cli.py patched goal related to documenting.

TARGET_WINDOW="Arch Linux Assistant - OpenGithuSDK Status Report - qutebrowser"
MESSAGE="😁 Updated docs for OpenGithubSDK"

find . -type f -name "*.py" | entr -r sh -c '
  python cli.py --mode goal --goal document_undocumented_files --args {{\"repo_name\": \"pyNance\"}} \
  && ./scripts/notify_qute.sh "${TARGET_WINDOW}" "${MESSAGE}"
'

