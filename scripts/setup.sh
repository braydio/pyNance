#!/usr/bin/bash

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
if [ -f requirements.txt ]; then
  pip install --upgrade pip
  pip install -r requirements.txt
else
  echo "Requirements file not found: requirements.txt"
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
  echo "Creating .env file from example.env..."
  cp backend/example.env backend/.env
fi

## 4. Set up Git hooks
echo "Linking Git hooks..."
git config core.hooksPath .githooks
chmod +x .githooks/*

## 5. Set up frontend
if [ -f frontend/package.json ]; then
  echo "Setting up frontend..."
  cd frontend

  if [ -f ../.nvmrc ]; then
    if command -v nvm &>/dev/null; then
      echo "Using Node version from .nvmrc..."
      nvm install
      nvm use
    else
      echo ".nvmrc found but nvm not installed. Continuing with system Node.js."
    fi
  elif [ -f ../.tool-versions ]; then
    echo "Found .tool-versions — consider using asdf for Node version management."
  fi

  if ! command -v npm &>/dev/null; then
    echo "npm not found. Please install Node.js and npm."
    exit 1
  fi

  echo "Installing frontend dependencies..."
  npm install
  cd ..
else
  echo "frontend/package.json not found. Skipping frontend setup."
fi

## 6. Run formatters on all tracks if pre-commit available
echo "Running formatters (black, isort, ruff)..."
if command -v pre-commit &>/dev/null; then
  pre-commit run --all-files || true
else
  echo "pre-commit not found — skipping formatter pass"
fi

echo "Setup complete!"
