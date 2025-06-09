#!/bin/bash

set -e

echo "[*] Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "[*] Installing dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt

if [ ! -f backend/.env ]; then
  echo "[*] Creating .env file from example.env..."
  cp backend/example.env backend/.env
fi

echo "[✓] Setup complete. Activate with 'source .venv/bin/activate'"
