#!/usr/bin/env bash
# Usage: ./env_prompt.sh [target_directory]
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 [target_directory]"
  exit 1
fi

DIR="$1"
cd "$DIR"
EXAMPLE_ENV="example.env"
TARGET_ENV=".env"

if [ ! -f "$EXAMPLE_ENV" ]; then
  echo "No $EXAMPLE_ENV found in $DIR"
  exit 1
fi

echo "# Generated .env from $EXAMPLE_ENV by interactive script" >"$TARGET_ENV"

while IFS= read -r line || [ -n "$line" ]; do
  if [[ "$line" =~ ^[[:space:]]*# ]]; then
    # comment, write to .env as-is
    echo "$line" >>"$TARGET_ENV"
  elif [[ "$line" =~ ^[[:space:]]*$ ]]; then
    # empty line
    echo "" >>"$TARGET_ENV"
  elif [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*) ]]; then
    VAR="${BASH_REMATCH[1]}"
    VALUE="${BASH_REMATCH[2]}"
    COMMENT=""
    # Try to find inline comment
    if [[ "$VALUE" =~ (.*)[[:space:]]*\#(.*) ]]; then
      VALUE="${BASH_REMATCH[1]}"
      COMMENT="${BASH_REMATCH[2]}"
    fi
    VALUE="${VALUE//\"/}" # strip double quotes
    VALUE="${VALUE//\'/}" # strip single quotes

    prompt="Enter value for $VAR"
    [ -n "$VALUE" ] && prompt="$prompt [default: $VALUE]"
    [ -n "$COMMENT" ] && prompt="$prompt  #${COMMENT}"

    read -rp "$prompt: " USER_INPUT
    if [ -z "$USER_INPUT" ]; then
      FINAL="$VALUE"
    else
      FINAL="$USER_INPUT"
    fi
    echo "$VAR=$FINAL" >>"$TARGET_ENV"
  else
    # fallback: write line as-is
    echo "$line" >>"$TARGET_ENV"
  fi
done <"$EXAMPLE_ENV"

echo ".env created at $DIR/$TARGET_ENV"
