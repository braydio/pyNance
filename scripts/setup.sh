#!/usr/bin/env bash

# Setup script for pyNance.
# Creates a virtual environment, installs dependencies, links Git hooks
# and prepares the frontend. Pass the --slim flag to install only the
# core dependencies from requirements-slim.txt and skip development
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
pip install --upgrade pip
if [ "$USE_SLIM" -eq 1 ]; then
  if [ -f requirements-slim.txt ]; then
    if ! pip install -r requirements-slim.txt; then
      echo "Dependency installation failed. Please check requirements." >&2
      exit 1
    fi
  else
    echo "Requirements file not found: requirements-slim.txt" >&2
    exit 1
  fi
else
  if [ -f requirements.txt ] && [ -f requirements-dev.txt ]; then
    if ! pip install -r requirements.txt -r requirements-dev.txt; then
      echo "Dependency installation failed. Please check requirements." >&2
      exit 1
    fi
  else
    echo "Requirements file not found: requirements.txt or requirements-dev.txt" >&2
    exit 1
  fi
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
