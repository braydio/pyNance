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

## 2. Activate and install backend dependencies
echo "Installing backend dependencies..."
source .venv/bin/activate
if [ -f backend/requirements.txt ]; then
  pip install --upgrade pip
  pip install -r backend/requirements.txt
else
  echo "Requirements file not found: backend/requirements.txt"
  exit 1
fi

echo "Installing dev dependendencies..."
if [ -f backend/requirements-dev.txt ]; then
  pip install -r backend/requirements-dev.txt
else
  echo "Dev requirements file not found: backend/requirements-dev.txt"
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

## 7. Start ChromaDB container if not already running
if ! curl --silent --fail http://localhost:8055/heartbeat >/dev/null; then
  if ! docker ps --format '{{.Names}}' | grep -q '^chromadb$'; then
    echo "ChromaDB not running — starting Docker container..."
    docker run -d --name chromadb -p 8055:8000 ghcr.io/chroma-core/chroma:latest
    sleep 5 # Give Chroma time to initialize
  else
    echo "Docker container 'chromadb' is present but unreachable — check port bindings."
  fi
else
  echo "ChromaDB is already running."
fi

## 8. Index documents if ChromaDB is reachable
echo "Checking ChromaDB availability..."
if curl --silent --fail http://localhost:8055/heartbeat >/dev/null; then
  echo "ChromaDB is running — updating vector index..."
  python scripts/chroma_index.py --diff-only
else
  echo "ChromaDB is still not available. Skipping index update."
fi

echo "Setup complete!"
