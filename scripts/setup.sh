#!/usr/bin/env bash

set -euo pipefail

echo "Setting up braydio/pyNance..."

## 1. Create virtual environment
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
else
  echo "Virtual environment already exists."
fi

## 2. Activate and install dependencies
echo "Installing dependencies..."
source .venv/bin/activate

# Allow using a slimmed-down requirements file with the --slim flag
REQ_FILE="requirements.txt"
if [[ ${1:-} == "--slim" ]]; then
  REQ_FILE="requirements-slim.txt"
fi

if [ -f "$REQ_FILE" ]; then
  pip install --upgrade pip
  pip install -r "$REQ_FILE"
else
  echo "Requirements file not found: $REQ_FILE"
  exit 1
fi

echo "Installing dev dependencies..."
if [ -f requirements-dev.txt ]; then
  pip install -r requirements-dev.txt
else
  echo "Dev requirements file not found: requirements-dev.txt"
  exit 1
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
echo "Running formatters (black, isort, ruff)..."
if command -v pre-commit &>/dev/null; then
  pre-commit run --all-files || true
else
  echo "pre-commit not found — skipping format check."
fi

echo "✅ pyNance setup complete!"
