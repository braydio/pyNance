# pyNance Documentation

This is the entry point for documentation.

## Start here (quickstart)

1. **Set up your environment**
   - From the repository root, run `bash scripts/setup.sh` to install Python/Node dependencies, install git hooks, and provision supporting services.
   - Copy `backend/example.env` to `backend/.env` and fill in connection details (e.g., `SQLALCHEMY_DATABASE_URI` for PostgreSQL). See [ENVIRONMENT_REFERENCE.md](./ENVIRONMENT_REFERENCE.md) for all variables, defaults, and troubleshooting tips.

2. **Run the API**
   - Apply database migrations before first boot: `flask --app backend.run db upgrade`.
   - Start the Flask server with `python backend/run.py` (or `flask --app backend.run run`) and verify `/health`.

3. **Run the frontend**
   - In a separate shell, `cd frontend && npm install && npm run dev` to launch the Vue dev server on the default port. If your backend runs on a custom host/port, update the Vite dev proxy.

4. **Run tests**
   - Backend: `pytest -q` from the repository root.
   - Frontend unit tests: `cd frontend && npm run test:unit`.

5. **Learn the workflow and processes**
   - Browse [docs/index/INDEX.md](./index/INDEX.md) for the categorized doc tree.
   - Refer to [docs/process/contributor-guide.md](./process/contributor-guide.md), [docs/process/repo_organization.md](./process/repo_organization.md), and [docs/process/execution-plan.md](./process/execution-plan.md) for contribution flow, repo layout, and planning cadence.
