#!/bin/bash

set -euo pipefail

echo "🔧 Setting up braydio/pyNance..."

# 1. Create virtual environment
if [ ! -d ".venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv .venv
else
  echo "✅ Virtual environment already exists."
fi

# 2. Activate and install backend dependencies
echo "📥 Installing backend dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Set up local Git hooks
echo "🔗 Linking Git hooks..."
git config core.hooksPath .githooks
chmod +x .githooks/*

# 4. Set up frontend
if [ -f frontend/package.json ]; then
  echo "📦 Setting up frontend..."
  cd frontend

  # Use Node version from .nvmrc if available
  if [ -f ../.nvmrc ]; then
    if command -v nvm &>/dev/null; then
      echo "🔢 Using Node version from .nvmrc..."
      nvm install
      nvm use
    else
      echo "⚠️  .nvmrc found but nvm not installed. Continuing with system Node.js."
    fi
  fi

  if ! command -v npm &>/dev/null; then
    echo "❌ npm not found. Please install Node.js and npm."
    exit 1
  fi

  echo "📥 Installing frontend dependencies..."
  npm install
  cd ..
else
  echo "⚠️  frontend/package.json not found. Skipping frontend setup."
fi

# 5. Run lint/formatters (optional)
echo "🧹 Running formatters (black, isort, ruff)..."
pre-commit run --all-files || true

echo "✅ Setup complete!"
