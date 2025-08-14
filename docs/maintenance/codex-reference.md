# CLAUDE.md – Project Developer Guide for pyNance

---

## Commands for Building, Linting, and Testing

### Backend
- **Run the Flask development server:**
```sh
flask run --app backend.app
```
- **Setup environment:**
```sh
cd backend
cp example.env .env
# Edit .env with real secrets/keys
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```
- **Run backend tests:**
```sh
pytest -q
```

### Frontend
- **Run the Vue development server:**
```sh
cd frontend
npm run dev
```
- **Lint frontend code (Prettier, ESLint):**
```sh
# Usually done automatically, or manually:
npm run lint
```

### Complete App
- **Run both backend and frontend for local dev:**
```sh
# In backend folder:
flask run --app backend.app
# In frontend folder:
npm run dev
```

---

## Architecture Overview

### Backend (`app/` folder)
- **Structure:**
  - `config/`: Environment variables, API config, constants
  - `extensions.py`: Import and initialization of SQLAlchemy
  - `models.py`: SQLAlchemy ORM models (accounts, transactions, users)
  - `routes/`: API REST endpoints for resources (accounts, transactions, charts, auth, etc.)
  - `services/`: Business logic and API integrations
  - `utils/` and `helpers/`: Utility functions
  - `certs/`: SSL/certificates if applicable
- **Main Files:**
  - `__init__.py`: App factory, blueprint registration
  - `run.py`: Starts the Flask app

### Frontend (`src/` folder)
- **Structure:**
  - `components/`: Vue 3 components, including tables and UI widgets
  - `views/`: Page layouts and main screens
  - `api/`: API layer calls to backend endpoints
  - `styles/` and `assets/`: Styling and static assets
  - `router/`: Frontend routing
- **Main Files:**
  - `App.vue`: Main Vue app component
  - `main.js`: Entry point, app setup

### Main Data Flow

- Frontend components call `/api/*` endpoints using the API Layer.
- Backend endpoints, defined in `routes/`, process requests, invoke `services/`, and interact with SQLAlchemy models.
- Data is returned to frontend in JSON format for visualization and interaction.
- User interactions trigger new API calls or client-side state updates.

---

This guide ensures a clear understanding of how to build, run, and comprehend the architecture of pyNance for effective development and maintenance.