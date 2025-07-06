#!/usr/bin/env bash

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}=============================="
echo -e "pyNance Unified Startup Script"
echo -e "==============================${NC}"

# 1. Check .env files before setup
for DIR in backend frontend; do
  if [ ! -f "$DIR/.env" ]; then
    if [ -f "$DIR/example.env" ]; then
      echo -e "${CYAN}${DIR}/.env not found. Launching interactive env setup...${NC}"
      bash scripts/env_prompt.sh "$DIR" || exit 1
      if [ -f "$DIR/.env" ]; then
        echo -e "${GREEN}Created $DIR/.env from interactive prompt.${NC}"
      else
        echo -e "${RED}Interactive script did not create .env in $DIR. Please check your setup.${NC}"
        exit 1
      fi
    else
      echo -e "${RED}${DIR}/.env and example.env missing. Cannot continue.${NC}"
      exit 1
    fi
  fi
done

echo -e "${YELLOW}[1/3] Running setup script...${NC}"
bash scripts/setup.sh

echo -e "${YELLOW}[2/3] Starting backend (Flask, port 5000)...${NC}"
(cd backend && flask run) &
BACKEND_PID=$!

echo -e "${YELLOW}[3/3] Starting frontend (npm, port 5173)...${NC}"
(cd frontend && npm install && npm run dev) &
FRONTEND_PID=$!

echo -e "${GREEN}Startup complete! Backend (5000), Frontend (5173) running.${NC}"
echo -e "${CYAN}Press Ctrl+C to stop all processes.${NC}"

trap "echo -e '\n${RED}Stopping backend and frontend...${NC}'; kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT

wait
