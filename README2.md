# pyNance Dashboard Setup (2025)

**pyNance** is a personal finance dashboard integrating **Plaid** and **Teller** APIs to visualize and manage your financial data. It uses **Flask** for the backend and **Vue.js** for the frontend.

---

## Project Structure

```
/backend/app/
  config/            # Environment, logging, constants, Plaid config
  routes/            # Flask API endpoints (accounts, transactions, charts, etc)
  helpers/           # Business logic helpers (Plaid, Teller, etc)
  sql/               # Raw SQL helpers
  models.py          # SQLAlchemy models
  extensions.py      # Flask extensions

/frontend/src/
  components/        # Vue.js Components (views, charts)
  views/             # Vue pages
  App.vue            # Main frontend app
```

---

## Quick Setup Guide

### 1. Clone the repository

```bash
git clone https://github.com/braydio/pyNance.git
cd pyNance
```

### 2. Create Environment Variables

Backend and frontend both require `.env` files.

**Backend**:

```bash

cp .env.example .env

```

Edit `.env` with your real credentials:

```dotenv
# Plaid Setup
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=sandbox

# Optional (if needed)
VITE_USER_ID_PLAID=your_user_id
VITE_APP_API_BASE_URL=http://localhost:5000/api

# Teller Setup (optional)
TELLER_APP_ID=your_teller_app_id
TELLER_WEBHOOK_SECRET=...
```

> Backend environment variables are loaded via `/backend/app/config/environment.py`.

**Frontend**:

```bash
cd frontend
cp .env.example .env
```

Customize frontend `.env` too if needed.

### 3. Install Backend Requirements

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run Backend

```bash
flask run --app app
```

(Starts Flask API at `http://127.0.0.1:5000`)

### 5. Install Frontend Requirements

```bash
cd frontend
npm install
```

### 6. Run Frontend

```bash
npm run dev
```

(Starts Vue frontend at `http://127.0.0.1:5173`)

---

## Important Configuration Files

| File | Purpose |
|:--|:--|
| `/backend/app/config/environment.py` | Loads `.env` for Flask server |
| `/backend/app/config/plaid_config.py` | Plaid API settings |
| `/backend/app/config/log_setup.py` | Logging setup |
| `/frontend/.env` | Frontend API and environment variables |
| `/BackendMap.txt` | Backend file structure map |
| `/FrontendMap.txt` | Frontend file structure map |

---

## Backend APIs

Base URL: `http://127.0.0.1:5000/api`

- `/accounts/get_accounts`
- `/transactions/get_transactions`
- `/charts/daily_net`
- `/charts/category_breakdown`
- `/accounts/refresh_accounts`

Plaid and Teller integrations handled in `/backend/app/helpers/`.

---

## Logs

Backend logs are output to `/backend/logs/app.log`. Logging behavior controlled by `/backend/app/config/log_setup.py`.

---

## Troubleshooting

- If you get database errors, check if `backend/app/data/pynance_dashroad.db` exists. Otherwise initialize it manually.
- For Plaid access issues, verify client_id, secret, and environment match (sandbox/development).
- Logs (`logs/app.log`) are your best friend!

---

## License

MIT License applies. See `LICENSE` file for details.
