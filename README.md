# pyNance Dashboard Setup (2025)

**pyNance** is a personal finance dashboard integrating **Plaid** and **Teller** APIs to visualize and manage your financial data. It uses **Flask** for the backend and **Vue&nbsp;3** with **Vite** and **TypeScript** for the frontend.

This project targets **Python&nbsp;3.11** and **Node&nbsp;20**.

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
cd backend
cp example.env .env
```

Edit `backend/.env` with your real credentials:

```dotenv
# Application
FLASK_ENV=development          # Options: production, development
CLIENT_NAME=pyNance-Dash       # Optional client name

# Logging
LOG_LEVEL=INFO                 # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
VERBOSE_LOGGING=false          # true enables custom 'VERBOSE' log level

# Database
DATABASE_NAME=example_database.db  # overrides default DB name
# Run `python scripts/generate_example_db.py` to create this file
# Run `python scripts/plaid_link_from_token.py` to import accounts from saved tokens

# Plaid Configuration
PLAID_CLIENT_ID=your_client_id_here
PLAID_SECRET_KEY=your_secret_here
PLAID_CLIENT_NAME=YourName     # (Optional) currently used for display
PLAID_ENV=sandbox              # Options: sandbox, development, production
PRODUCTS=transactions,investments  # Comma-separated list of products

# Teller Configuration
TELLER_APP_ID=your_teller_app_id_here
TELLER_WEBHOOK_SECRET=your_webhook_secret_here

# Dev/Test Variables (optional)
VARIABLE_ENV_TOKEN=optional_test_token
VARIABLE_ENV_ID=optional_test_id
```

> These variables are loaded via `/backend/app/config/environment.py`.

**Certificates**:

Place your Teller certificates in:

```bash
backend/app/certs/
  ├── certificate.pem
  └── private_key.pem
```

See `/backend/app/certs/README.md` for details.

**Frontend**:

```bash
cd frontend
cp example.env .env
```

Edit `frontend/.env` with:

```dotenv
VITE_APP_API_BASE_URL=/api
# ... other VITE_ variables as needed
```

### 3. Run the setup script

```bash
bash scripts/setup.sh [--slim]
```

This command creates the virtual environment, installs all Python (including dev) and Node dependencies,
links pre-commit hooks, and copies the example `.env` files.

### 3a. Manual dependency install
If you prefer manual setup, activate your virtual environment and run:

```bash
pip install -r requirements-dev.txt
pip install pre-commit flask
links pre-commit hooks and copies the example `.env` files if needed.

### Manual dependency install

If you prefer to configure the environment yourself, run:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt  # installs Flask, pre-commit and other packages
npm install
pre-commit install
```


Run `pip install -r requirements-dev.txt` and `npm install` **before** executing
`pre-commit run --all-files` or `pytest`.

### 4. Run Backend

```bash
flask run --app backend.run
```

(Starts Flask API at `http://127.0.0.1:5000`)

### 5. Run Frontend

```bash
npm run dev
```

(Starts Vue frontend at `http://127.0.0.1:5173`)

### 6. Run Tests

```bash
pytest -q
pre-commit run --all-files
```

All tests should pass when dependencies are installed.

---

## Important Configuration Files

| File | Purpose |
|:--|:--|
| `/backend/app/config/environment.py`    | Loads environment variables (FLASK_ENV, CLIENT_NAME, PLAID_*, TELLER_*, etc.) |
| `/backend/app/config/plaid_config.py`   | Plaid API client setup (PLAID_CLIENT_ID, PLAID_SECRET_KEY & PLAID_ENV) |
| `/backend/app/config/log_setup.py`      | Logging configuration (LOG_LEVEL, VERBOSE_LOGGING, handlers) |
| `/backend/app/config/constants.py`      | Application constants & database URI (data paths, themes, etc.) |
| `/backend/app/config/paths.py`          | Directory paths auto-creation (DATA_DIR, LOGS_DIR, CERTS_DIR, etc.) |
| `/backend/app/certs/README.md`          | Instructions for placing Teller certificate.pem & private_key.pem |
| `/frontend/example.env`                 | Frontend environment variables example |
| `/frontend/.env`                        | Frontend environment variables |

Refer to [`docs/index/INDEX.md`](docs/index/INDEX.md) for a full documentation map.

---

## Backend APIs

Base URL: `/api`

When using the Vue development server, requests to `/api` are automatically
proxied to your Flask backend (default `http://127.0.0.1:5000`). This avoids
CORS issues when accessing the frontend from another device. If you call the
backend directly (without the proxy), prepend the host and port, e.g.
`http://127.0.0.1:5000/api`.

- `/accounts/get_accounts`
- `/transactions/get_transactions`
- `/charts/daily_net`
- `/charts/category_breakdown`
- `/accounts/refresh_accounts`

  Optional JSON body fields:

  - `account_ids` – list of account IDs to refresh
  - `start_date` – optional `YYYY-MM-DD` start date
  - `end_date` – optional `YYYY-MM-DD` end date

### Transaction Rules

Transaction rules let you define patterns for merchant names or amounts and apply category changes automatically. Manage rules at `/api/rules`. See [docs/backend/features/transaction_rules.md](docs/backend/features/transaction_rules.md) for details.

Plaid and Teller integrations handled in `/backend/app/helpers/`.

## Running Tests

Ensure dependencies are installed before executing the test suite.
For a lightweight install without forecasting or LLM modules, use
`requirements-slim.txt`:

```bash
pip install -r requirements-slim.txt
pytest -q
```


---

## Logs

Backend logs are output to `backend/app/logs/app.log` (and `backend/app/logs/verbose.log` if `VERBOSE_LOGGING=true`). Logging behavior is controlled by `/backend/app/config/log_setup.py`.

---

## Troubleshooting

- If you get database errors, check if `backend/app/data/<DATABASE_NAME>.db` exists (default `developing_dash.db` when `PLAID_ENV=sandbox`, otherwise `main_dash.db`). Otherwise initialize it manually.
- If you get database errors, ensure the file specified by `DATABASE_NAME` exists in `backend/app/data/`. If not, generate it with `python scripts/generate_example_db.py`.
- If you already have Plaid tokens saved, run `python scripts/plaid_link_from_token.py` to seed accounts.
- For Plaid access issues, verify `PLAID_CLIENT_ID`, `PLAID_SECRET_KEY`, and `PLAID_ENV` values.
- Check logs in `backend/app/logs/` (e.g. `app.log`, `verbose.log`) for details.
- If `pre-commit` or `flask` are missing, activate your virtual environment and run `pip install -r requirements-dev.txt`.
- If frontend commands fail due to missing packages, run `npm install` inside `frontend/`.
---

## License

MIT License applies. See `LICENSE` file for details.
