# CLAUDE.md – Project Assistant Guide for pyNance

This document is for code assistants (Claude, GPT-4, Deepseek, etc.) to understand the **pyNance** project, its conventions, and the best way to help.

---

## Project Overview

**pyNance** is a personal finance dashboard that integrates with **Plaid** and **Teller** APIs for account aggregation, transaction visualization, and category analytics.

- **Backend:** Python 3.11, Flask, SQLAlchemy, Flask-Alembic
- **Frontend:** Vue 3/Vite, Tailwindcss
- **Data:** SQLite using Flask-SQLAlchemy

---

## File & Directory Structure

### pyNance/backend/app/

- config/ # Environment, logging, constants, Plaid/Teller API config
- helpers/ # Misc support utilities
- models.py # SQLAlchemy models
- routes/ # API endpoints (accounts, transactions, charts)
- extensions.py # SQLAlchemy import

### pyNance/frontend/src/

- components/ # All components used by Single Page Apps
- views/ # Main page layouts
- App.vue # Main app entrypoint

### pyNance/

- scripts/ # Setup, DB, and ETL scripts
- docs/ # Documentation (see docs/index/INDEX.md for map)
-

- **Config files:**

  - `backend/app/config/environment.py`, `.env` – environment vars (credentials, dev/prod)
  - `backend/app/config/plaid_config.py` – Plaid API keys/settings
  - `backend/app/config/constants.py` – Application constants and default values

- **Frontend tables:**
  - `frontend/src/components/tables/TransactionsTable.vue` – Main transactions display
  - `frontend/src/components/tables/UpdateTransactionsTable.vue` – For editing/updating transactions

---

## Coding & API Conventions

- **Backend:**

  - Use **type hints** throughout (Python 3.11+)
  - API follows REST principles, typically `/api/resource` (e.g. `/api/transactions`)
  - All sensitive data is set via environment variables (`.env` or `backend/app/config/`)
  - DB layer uses SQLAlchemy models
  - Logging is handled by `backend/app/config/log_setup.py` and controlled by env

- **Frontend:**
  - Components are written in Vue 3 with TypeScript and follow PascalCase file naming
  - Table UIs are in `frontend/src/components/tables/`
  - API calls use `/api/*` endpoints (see backend routes)
  - Use existing utility/helper modules for API/data formatting

---

## How to Help Effectively

- If editing a **table component** (e.g. TransactionsTable.vue):

  - It’s found in `frontend/src/components/tables/`
  - Use both the `category` and `icon_url` fields for Plaid-based display logic as required
  - If unsure which table is the “main” one for transactions, prefer `TransactionsTable.vue` or `UpdateTransactionsTable.vue`

- **For backend changes:**

  - Place config/secrets in the relevant file under `backend/app/config/` or `.env`
  - Ensure all new endpoints or models have clear docstrings and type hints
  - Tests can be run via `pytest -q`; new code should have basic test coverage

- **General:**
  - Always update docstrings and function signatures if you change code behavior
  - Prefer explicit imports; keep dependencies minimal
  - If adding new scripts or ETL logic, place in `/scripts/` and document usage at the top of the file

---

## Project Commands

**Backend Setup:**

```sh
cd backend
cp example.env .env
# Edit .env with real secrets/keys
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
flask run --app backend.app  # Flask API
# or for Vue dev server:
cd frontend && npm run dev
Tests:

Run backend tests: pytest -q

Commit frequently; run tests before submitting PRs

FAQ / Assistant Tips
If a prompt references a table like “Transactions table”, assume it is frontend/src/components/tables/TransactionsTable.vue unless told otherwise.

If asked to “use Plaid icon and category”, use both fields together in the cell render logic.

Always check for and document any new environment variables or secrets.

Do not duplicate logic between backend and frontend helpers.

Reference docs/index/INDEX.md for more project documentation.

If in doubt, ask for clarification—but make a best guess based on this structure before requesting more info.

Contribution Etiquette
Keep code clean and idiomatic (PEP8 for Python, Prettier for Vue)

Document any new scripts or major logic

Leave all sensitive keys/secrets in .env or config files (never hardcode)

Comment major changes in the relevant section at the top of this file

---

# CLAUDE.md for Claude Code Context

---

## **pyNance Directory Map**

---

### **Backend (`backend/`)**

```

backend/
├── .flaskenv
├── Procfile
├── cron_sync.py
├── docker-compose.yml
├── example.env
├── load_transactions.py
├── recurring_flags.txt
├── run.py
├── app/
│ ├── **init**.py # Main Flask app/init, all blueprints, setup, CORS, error handlers, DB, etc
│ ├── extensions.py # SQLAlchemy import
│ ├── models.py # All SQLAlchemy models (accounts, users, transactions, etc)
│ ├── certs/
│ ├── cli/
│ ├── config/
│ ├── helpers/
│ ├── routes/
│ │ ├── **init**.py
│ │ ├── accounts.py
│ │ ├── auth.py
│ │ ├── categories.py
│ │ ├── charts.py
│ │ ├── health.py
│ │ ├── recurring.py
│ │ ├── teller.py
│ │ └── transactions.py
│ ├── services/
│ │ └── (service-layer files: api abstraction, business logic)
│ ├── sql/
│ │ └── (programmatic queries/business logic)
│ ├── static/
│ │ └── (static files for Flask serving)
│ └── utils/
│ └── (utility functions for backend)
├── dev/
├── migrations/
├── scripts/
└── temp_migrations/

```

---

### **Frontend (`frontend/`)**

```

frontend/
├── .editorconfig
├── .gitattributes
├── .gitignore
├── .husky/
├── .prettierrc.json
├── Dev_Checklist.md # Large dev onboarding/progress doc
├── README.md
├── backups/
├── cypress.config.js
├── cypress/
├── eslint.config.js
├── example.env
├── frontend_lint.txt
├── index.html
├── jsconfig.json
├── package-lock.json
├── package.json
├── public/
├── scripts/
├── src/
│ ├── App.vue
│ ├── OldAccountReorder.vue
│ ├── auto-imports.d.ts
│ ├── components.d.ts
│ ├── api/
│ │ ├── MIGRATIONS_CHECKLIST.md
│ │ ├── accounts.js
│ │ ├── accounts_link.js
│ │ ├── arbitrage.js
│ │ ├── categories.js
│ │ ├── charts.js
│ │ ├── recurring.js
│ │ ├── teller.js
│ │ └── transactions.js
│ ├── assets/
│ ├── components/
│ │ ├── **tests**/
│ │ ├── backups/
│ │ ├── base/
│ │ ├── charts/
│ │ ├── forecast/
│ │ ├── forms/
│ │ ├── layout/
│ │ ├── modals/
│ │ ├── recurring/
│ │ ├── tables/
│ │ ├── ui/
│ │ ├── unused/
│ │ └── widgets/
│ ├── composables/
│ ├── main.js
│ ├── mocks/
│ ├── router/
│ ├── services/
│ ├── styles/
│ ├── utils/
│ └── views/
├── stats.html
├── tailwind.config.js
├── vite.config.js
└── workflow

```

---

## **Context & Key Points for a `CLAUDE.md` File**

### **High-level project purpose**

- Full-stack personal finance app.
- Frontend: Vue 3 + Vite + Tailwind, modular component structure, composables for state logic, API-layer abstraction.
- Backend: Flask app using blueprints for modular REST routes, SQLAlchemy ORM, Marshmallow serialization, service-layer for business logic, Postgres (via SQLAlchemy).

### **Design & Data Flow**

- API endpoints handled by Flask blueprints, matching FE `/api/*.js` calls.
- Typical pattern: `/api/route.js` → `app/routes/route.py` → `services/` → `models.py`
- State management is handled per-page/composable on FE, not via Vuex or Pinia (as far as visible).
- Charts/tables are driven by backend API data, not by static/mocked data.
- Modal, chart click, and drill-down: event → state set → modal opens with filtered array (client-side).

### **Dev Process & Structure**

- Organized by feature/concern on both FE/BE (`charts`, `accounts`, `categories`, `transactions`, etc.).
- Active use of TypeScript d.ts for FE type hints, Prettier/ESLint enforced, Cypress for E2E testing.
- Dev checklist and migrations checklist for onboarding.

### **Planned/Noted Features**

- Frontend code, comments, and dev checklist suggest: More insights, analytics, advanced drill-downs, recurring tx logic, possibly future ML-driven prediction.
- Backend has full recurring tx logic, custom queries for analytics, and modular structure for rapid expansion.

---

## **Summary**

This is a modular, maintainable full-stack Vue/Flask finance app with strong separation of concerns. API-first design. All state/data is live-loaded from the backend. Modal and drill-down logic always filters from the most up-to-date loaded array in the FE, not from re-calling the backend (unless explicitly needed).

**If you need a sample or further code context for any file/feature, let me know!**
```
