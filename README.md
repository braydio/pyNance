# pyNance Dashboard

**pyNance** is a personal finance dashboard integrating Plaid and Teller APIs to visualize and manage your financial data. It uses Flask for the backend and Vue.js for the frontend.

---

## Features

- Link bank accounts via Plaid or Teller
- Sync transactions and balances
- Auto-categorize transactions using Plaid's category tree
- View net assets, account trends, and more
- Built-in transaction editor with category overrides
- Logs and debug tools for development

---

## Project Structure

```
backend/app/
├── config/          # Environment, logging, paths, plaid setup
│   ├── environment.py
│   ├── plaid_config.py
│   ├── log_setup.py
│   ├── constants.py
│   └── paths.py
├── routes/          # Flask blueprints (API endpoints)
│   ├── plaid_transactions.py
│   ├── teller.py
│   ├── accounts.py
│   └── ...
├── helpers/         # SDK integrations and utility wrappers
│   └── plaid_helpers.py
├── sql/             # Business logic for database interactions
│   ├── account_logic.py
│   └── category_logic.py
├── models.py        # SQLAlchemy models
├── extensions.py    # Database and Flask extensions
└── __init__.py      # App factory and blueprint registration

frontend/src/
├── components/      # Vue components for views and charts
├── views/           # Pages and dashboard screens
└── App.vue          # Main app entry
```

---

## Environment Setup

Copy the example environment template and configure your secrets:

```bash
cp .env.example .env
```

Example `.env` values:

```env
# Plaid Setup
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET_KEY=your_secret
PLAID_ENV=sandbox
VITE_USER_ID_PLAID=your_name

# Frontend Specificic - API Base
# Change this if not accessing web page from same device
VITE_APP_API_BASE_URL=http://localhost:5000/api

# Teller Setup (optional)
TELLER_APP_ID=your_teller_app_id
TELLER_WEBHOOK_SECRET=...
```

> Env variables are loaded by `config/environment.py`.
> Plaid SDK config is defined in `config/plaid_config.py`.

---

## Logging

Logs are configured in `config/log_setup.py` and output to `logs/app.log`. You can adjust verbosity via:

```python
from app.config import verbose_logging
```

Transaction-level logs can be toggled by setting `verbose_logging = True`.

---

## Plaid Integration

Plaid SDK is used via `plaid_helpers.py` for endpoints like:

- `/transactions/get`
- `/accounts/get`
- `/item/get`

`/categories/get` is not supported in the SDK, so we call it directly using `requests.post()`.

On `/refresh_accounts`, pyNance:

- Refreshes account balances
- Updates transactions
- Refreshes Plaid categories

---

## Running Locally

```bash
# Install backend deps
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start Flask
flask run --app app

# In a second terminal
cd frontend
npm install
npm run dev
```

---

## Roadmap

- Add recurring transaction detection
- Sync investments and liabilities
- CSV import for transaction information

---

## License

MIT License. See LICENSE file.

