#!/usr/bin/env bash

# Setup script for pyNance.
# Creates a virtual environment, installs dependencies, links Git hooks
# and prepares the frontend. Use the --slim flag to install only core
# dependencies from requirements-slim.txt and skip heavy development
# packages.

set -euo pipefail

USE_SLIM=0
for arg in "$@"; do
  case "$arg" in
    --slim)
      USE_SLIM=1
      ;;
    *)
      echo "Usage: $0 [--slim]"
      exit 1
      ;;
  esac
done

echo "Setting up braydio/pyNance..."

## 1. Create virtual environment
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
else
  echo "Virtual environment already exists."
fi

## 2. Activate and install dependencies
source .venv/bin/activate

if [ "$USE_SLIM" -eq 1 ]; then
  REQ_FILE="requirements-slim.txt"
  echo "Installing slim dependencies from $REQ_FILE..."
else
  REQ_FILE="requirements.txt"
  echo "Installing dependencies from $REQ_FILE..."
fi

if [ -f "$REQ_FILE" ]; then
  pip install --upgrade pip
  pip install -r "$REQ_FILE"
else
  echo "Requirements file not found: $REQ_FILE"
  exit 1
fi

if [ "$USE_SLIM" -eq 0 ]; then
  echo "Installing dev dependencies..."
  if [ -f requirements-dev.txt ]; then
    pip install -r requirements-dev.txt
  else
    echo "Dev requirements file not found: requirements-dev.txt"
    exit 1
  fi
else
  echo "Slim mode: skipping dev dependency installation."
fi

## 3. Create .env if missing
if [ ! -f backend/.env ]; then
  echo "Creating .env file from backend/example.env..."
  cp backend/example.env backend/.env
fi

## 4. Set up Git hooks
echo "Linking Git hooks..."
git config core.hooksPath .githooks
chmod +x .githooks/* || true

## 5. Frontend setup (if present)
if [ -d frontend ] && [ -f frontend/package.json ]; then
  echo "Setting up frontend..."
  cd frontend

  if [ -f ../.nvmrc ] && command -v nvm &>/dev/null; then
    echo "Using Node version from .nvmrc..."
    nvm install
    nvm use
  fi

  if ! command -v npm &>/dev/null; then
    echo "npm not found. Please install Node.js and npm."
    exit 1
  fi

  echo "Installing frontend dependencies..."
  npm install
  cd ..
else
  echo "No frontend setup detected. Skipping."
fi

## 6. Run formatters on all files if pre-commit is installed
if command -v pre-commit &>/dev/null; then
  echo "Running formatters (black, isort, ruff)..."
  pre-commit run --all-files || true
else
  echo "pre-commit not found — skipping format check."
fi

echo "✅ pyNance setup complete!"
