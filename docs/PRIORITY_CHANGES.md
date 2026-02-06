
---

# pyNance State of the Repo and Implementation Roadmap

## Repo mapping with evidence and boundary notes

pyNance is an “API + SPA + Postgres” monorepo: a Flask backend under `backend/`, a Vue 3/Vite frontend under `frontend/`, and a significant amount of operational and planning documentation under `docs/`.

### Top-level directories and intended purposes

A repo-maintained map classifies these top-level areas (and is internally consistent with the README’s positioning of the project as Flask/Vue/Postgres + Plaid).

* `backend/` — Flask API + CLI + Alembic/Flask-Migrate migrations; this is the canonical server runtime.
* `frontend/` — Vue 3/Vite app (“dashvue” package) with Cypress/Vitest scripts.
* `docs/` — extensive documentation tree that “mirrors the backend structure,” plus roadmaps, maintenance audits, integration notes, and environment reference docs.
* `scripts/` — repo-level automation and validation scripts (format/lint/type checks, docs checks, etc.).
* `tests/` — pytest suite for routes/services; heavy use of stubbing and dynamic module loading.
* `workers/` — a small, single-purpose Cloudflare Worker that forwards Plaid webhooks to the backend.
* `tools/` — “one-off utilities” (e.g., symbol mapping).
* `chromadb` — classified in the internal map as “stale” (a PostScript snapshot) without runtime integration.

  <!-- COMMENT: On main today, `chromadb/` does not appear to exist at repo root; this item is likely outdated as a directory-level statement, though the *docs map* may still mention it. -->

### Backend vs frontend boundary

The hard boundary is HTTP. The frontend uses an Axios client that defaults to `VITE_APP_API_BASE_URL` or `/api`, and it calls routes like `/accounts/get_accounts`, `/transactions/get_transactions`, `/charts/*`, and `/dashboard/*`.

On the backend, the Flask application factory registers many feature-domain blueprints (accounts, transactions, charts, forecast, goals, investments, planning, docs export, etc.). Anything not imported and registered there is effectively dead code.

### Config and environment files, patterns, and secrets risk

There are multiple parallel “env template” and “example env” conventions, and they are not aligned across docs, scripts, and code:

* Template env files exist for backend and frontend (`backend/.env.example`, `frontend/.env.example`) as part of “security hardening” effort.
* The frontend env template includes `PHONE_NBR` (a phone-number-shaped value) and a `VITE_USER_ID_PLAID` field. Even if this is a placeholder, it increases the chance a developer pastes real PII into a file that looks “template-ish.”
* Docs and tooling still refer to `backend/example.env` as the source of truth (“copy backend/example.env to backend/.env”).

  <!-- COMMENT: As of main today, `backend/example.env` does not exist; references to it are likely stale and will break onboarding/scripts. -->
* The backend bootstrap script (`backend/scripts/setup.sh`) also copies from `backend/example.env` into a `backend/.env`, not from `.env.example`.

  <!-- COMMENT: This is currently a real break: the script copies a file that isn’t present on main. -->

These patterns imply at least three env “templates” can exist simultaneously (`backend/.env.example`, `backend/example.env`, `frontend/.env.example`), plus the actual `.env` files used locally—making drift and accidental leakage more likely.

The `.gitignore` has been expanded to ignore `.env`, `.env.*`, shell profiles, and other secret-adjacent files. That is a strong baseline—but it also means there’s no structural guardrail preventing “example” templates from containing values that *look* safe but are actually sensitive (e.g., phone numbers, user IDs).

### Scripts, utilities, migrations, and import/export paths

Evidence of “operational surface area” includes:

* Backend dev bootstrap: `backend/scripts/setup.sh` starts Postgres via `backend/docker-compose.yml`, waits for readiness, then runs migrations.
* Backend `docker-compose.yml` defines Postgres and a `fidelity_worker` service. The `fidelity_worker` appears to depend on a `backend/fidelity_worker` directory, but it does not show up in code searches beyond compose, and there is an unrelated, currently broken/unwired `fidelity.py` route file (see “dead folders / dead code” below).

  <!-- COMMENT: The compose mismatch is still accurate (worker dir missing on main). The mention of an in-tree `backend/app/routes/fidelity.py` is likely outdated: that file does not appear to exist on main today. -->
* Repo-level validation script `scripts/validate-dev.sh` runs Python format/lint/type-check/test steps and frontend lint/format/test steps, and is invoked in CI.
* CLI import/backfill tools are registered with Flask’s CLI (import accounts/plaid accounts/plaid tokens, backfill history, reconcile items, seed dev).

### Inconsistencies and dead/unclear areas

The repo’s own “Repository Map” explicitly flags several route modules as stale/unregistered and recommends moving them to an `/archive` folder or rewriting them.

Concrete examples:

* `backend/app/routes/product_transactions.py` is FastAPI-specific (`APIRouter`, Pydantic) and does not match the Flask blueprint registration model used in `create_app()`, so it is effectively dead in the current stack.

  <!-- COMMENT: On main today, `backend/app/routes/product_transactions.py` does not appear to exist; this specific example is likely outdated even if the repo map still references it. -->
* `backend/app/routes/fidelity.py` imports `app.services.fidelity_service.FidelityService`, which does not correspond to the current backend layout (services live under `backend/app/services/`, not `app/services/`), and it is not registered in the app factory list.

  <!-- COMMENT: On main today, `backend/app/routes/fidelity.py` does not appear to exist; this specific example is likely outdated. -->
* `backend/app/routes/plaid_transfer.py` creates its own `Flask(__name__)` app and exposes an ad-hoc route (`/pay_credit_card`) with “Jane Doe / [jane@example.com](mailto:jane@example.com)” placeholders and direct secret usage. This is not wired into `create_app()` and is a clear candidate for archival.

  <!-- COMMENT: On main today, `backend/app/routes/plaid_transfer.py` does not appear to exist; this specific example is likely outdated. -->
* Duplicate dependency lockpoints: there is both a root `requirements.txt` and `backend/requirements.txt`, and they appear identical. This increases the chance CI, docs, and local development drift.

  <!-- COMMENT: Both files exist on main, but they are not identical: root includes dev deps (e.g., pytest/pytest-cov) that backend/requirements.txt omits. The drift risk still applies. -->

## Code quality, architecture, and data flow assessment

### Structure and modularity

The backend uses a recognizable separation between:

* **Routes** (Flask blueprints) under `backend/app/routes/*`, registered in `backend/app/__init__.py`.
* **“SQL logic” modules** (domain logic + persistence) under `backend/app/sql/*`; a key example is `account_logic.py`, which contains both business rules (like rate-limit cooldown, refresh staleness detection) and persistence/upsert logic.
* **Helpers** for external APIs (Plaid) under `backend/app/helpers/*`; `plaid_helpers.py` includes typed request objects, pagination for `/transactions/get`, and “don’t leak tokens” logging intent.
* **Services** for more coherent “unit-of-work” behavior do exist, notably `backend/app/services/plaid_sync.py` which implements delta-based `transactions/sync` with cursor persistence.

  <!-- COMMENT: Confirmed on main: `backend/app/services/plaid_sync.py` exists and implements cursor-based sync. -->

However, business logic is still frequently embedded in route modules or in large, catch-all `app/sql/*` modules:

* `backend/app/routes/plaid_transactions.py` includes token exchange, item/account persistence, and a “refresh” operation that calls into `account_logic.refresh_data_for_plaid_account`.
* `backend/app/routes/transactions.py` implements normalization/parsing helpers and handles “create rule from edits” inline, then calls `account_logic` and other modules.

Net: the repo is mid-transition from “routes contain behavior” toward “services encapsulate flow,” but it hasn’t been fully consolidated.

### Consistency: style, error handling, logging, validation, types

Strengths:

* Strong lint/format/test posture in CI: a workflow enforces Black/isort/Ruff, runs pytest, and runs the full `scripts/validate-dev.sh` plus docs checks.
* Some modules are annotated and deliberately defensive: `services/plaid_sync.py` uses types and handles Plaid SDK version differences, and it always wraps DB operations in commit/rollback cycles.
* There are tests designed to prevent a common refactor footgun: `tests/test_model_field_validation.py` parses Python AST to ensure route/helper code does not reference non-existent SQLAlchemy model attributes.

Weaknesses / drift:

* Portable tooling issue: `.pre-commit-config.yaml` pins a user-specific Python interpreter path (`/home/braydenchaffee/...`) which will fail everywhere else.
* Configuration “truth” is inconsistent across code and docs: configuration code explicitly “avoids Flask-specific environment variables and relies solely on ENV,” but docs and tests still reference `FLASK_ENV`.
* Request validation is ad-hoc. Some endpoints validate inputs carefully (e.g., transaction update validates date/amount and tag normalization), but there’s no unified request-schema layer across the backend.

### Coupling and duplication

Clear duplication exists between:

* Plaid transaction ingestion flows:

  * The **legacy** flow fetches potentially large ranges using `/transactions/get` via `helpers.plaid_helpers.get_transactions()` and then individually `SELECT ... WHERE transaction_id=<id>` per transaction to upsert in `account_logic.refresh_data_for_plaid_account`.
  * A **newer** delta-based flow exists in `services/plaid_sync.py` that uses `transactions/sync` and cursor persistence.
    This “two ingestion engines” situation is a classic maintenance risk: it doubles the surface area for bugs and causes docs to become ambiguous.

* Transaction update endpoints: `transactions.py` has both `/update` (PUT) and `/user_modify/update` with overlapping logic.

* Requirements files: root vs backend copy.

  <!-- COMMENT: The duplication exists; however they are not identical on main (root includes dev deps). -->

### Data flow: ingestion → normalization → persistence → serving to UI

A practical end-to-end path for transactions now looks like:

* **Frontend** calls:

  * `/api/plaid/transactions/generate_link_token`, `/exchange_public_token` (Link flow), and then triggers refresh/sync endpoints and account/transaction reads via `/api/accounts/*` and `/api/transactions/*`.
* **Backend Plaid link flow** persists:

  * `PlaidItem` (item_id/access_token/product/institution) and `PlaidAccount` rows per account_id, then inserts/updates `Account` records via `account_logic.upsert_accounts`.
* **Normalization**:

  * The ingestion path normalizes balances (`normalize_balance`), transaction amounts (`normalize_amount`), categories (both legacy `category[]` and Plaid PFC fields), and merchant metadata.
* **Persistence**:

  * Transactions are stored as SQLAlchemy models; the transaction model includes category linkage and stores personal_finance_category fields, and other modules persist raw/aux Plaid metadata for audit/rehydration.
* **Serving to UI**:

  * `/api/transactions/get_transactions` delegates to `account_logic.get_paginated_transactions`, which joins `Transaction`, `Account`, and `Category`, filters hidden/internal transactions, and returns a serialized response.
  * A short-lived in-memory cache exists for transaction pages (TTL 90s, only first 5 pages).

Webhooks:

* There is a Cloudflare Worker that forwards `POST /api/webhooks/plaid` traffic to the backend’s `/api/webhooks/plaid`.
* The backend webhook handler validates a `Plaid-Signature` header using `PLAID_WEBHOOK_SECRET`, logs events (including persistence to a `PlaidWebhookLog` table), and triggers:

  * transactions refresh on `TRANSACTIONS:SYNC_UPDATES_AVAILABLE` / `DEFAULT_UPDATE` by iterating `PlaidAccount` records for the item and calling `account_logic.refresh_data_for_plaid_account`.

    <!-- COMMENT: Confirmed on main: `plaid_webhook.py` triggers `account_logic.refresh_data_for_plaid_account` (legacy refresh), not the cursor-based `services/plaid_sync.py` path. -->
  * investment-related refreshes on `INVESTMENTS_TRANSACTIONS` and `HOLDINGS`.

## Reliability, security posture, and likely performance hotspots

### Testing and reliability posture

The repository has meaningful tests and CI gates:

* CI runs formatting, linting, tests, “validate-dev,” and docs checks.
* Unit tests use “module stubbing” against Flask blueprints to keep tests fast and avoid real DB dependency.
* Specialized AST-based tests enforce model-field correctness.

Testability blockers still exist:

* Many route modules import `app.config` and other modules at import time, requiring tests to monkeypatch `sys.modules` early. This is workable but indicates dependency injection is not first-class.

### Security posture and key risks

High-risk items visible from code + docs:

* **No obvious authentication boundary**: The frontend API client sends no auth headers and many endpoints accept `user_id` in request bodies/params, implying “user scoping” is largely client-trusted.
  Without a real auth/session layer, “multi-user” exposure becomes likely (IDOR-style risks) if deployed beyond a single-user context.

* **CORS is enabled globally with default settings** (`CORS(app)`), which, paired with weak/no auth, increases accidental exposure risks if the backend is reachable publicly.

* **Sensitive token material logged**: `plaid_transactions.exchange_public_token_endpoint()` logs the Plaid access token at INFO level (“Token exchange successful. Access Token: …”). This is a direct credential leakage risk into logs.

  <!-- COMMENT: Confirmed on main: access token is logged during exchange. -->

  This contradicts the intent documented in `plaid_helpers.py`, which states logging should “avoid emitting sensitive token material.”

* **Env templates contain PII-shaped fields**: `frontend/.env.example` includes `PHONE_NBR=+10000000000`. Even as a placeholder, it normalizes the idea of storing phone numbers in env files.

* **Legacy route modules include highly unsafe patterns**:

  * `plaid_transfer.py` embeds a standalone Flask app and includes placeholder “Jane Doe” user info and direct secret usage, and is not registered in the app factory.

    <!-- COMMENT: This specific file does not appear to exist on main today; treat as outdated example. -->
  * `fidelity.py` references a missing service and is not registered.

    <!-- COMMENT: This specific file does not appear to exist on main today; treat as outdated example. -->

Positive security signals:

* `.gitignore` is explicitly curated to ignore `.env`/shell profile files and reduce accidental secret commits.
* Webhook signature validation is implemented for Plaid webhooks using HMAC compare-digest.

### Performance hotspots and scalability pain points

The backend already contains signs of performance-aware engineering, but there are likely hotspots:

* **Transactions ingestion**:

  * `account_logic.refresh_data_for_plaid_account` uses `/transactions/get` pagination and then performs per-transaction queries (`Transaction.query.filter_by(transaction_id=txn_id).first()` inside a loop). That pattern is “N queries” and will become a bottleneck on large histories.
  * The lookback is up to 680 days by default, which amplifies ingestion load and increases the likelihood of API throttling and long DB transactions.

* **Transactions serving**:

  * `get_paginated_transactions` computes `total = query.order_by(None).count()` which can be expensive if filtering is broad and indices are insufficient.
  * A small in-memory cache exists (TTL 90s, pages ≤5), which helps in low-concurrency situations but does not scale across processes/containers.

* **Delta-based sync exists but is not the primary path**:

  * The repo includes a well-structured `services/plaid_sync.py` that implements cursor-based `transactions/sync` and bulk-ish atomic batches, which is more scalable than repeatedly pulling long lookback windows.
    Aligning the webhook/refresh path with this service is a major “high leverage” opportunity.

---

## Bottom comments (necessary)

1. **Outdated file examples in “dead/legacy modules”**: The report cites `backend/app/routes/product_transactions.py`, `backend/app/routes/fidelity.py`, and `backend/app/routes/plaid_transfer.py`. On the current `main` branch, these specific files **do not appear to exist**. The *concept* (“repo map lists stale modules / dead code exists or existed”) may still be valid, but these are no longer reliable concrete examples.

2. **`chromadb/` directory callout**: The report states a top-level `chromadb` directory exists and is stale. On current `main`, that directory **does not appear to exist**.

3. **Requirements file identity**: The report says root `requirements.txt` and `backend/requirements.txt` are identical. On current `main`, they are **not identical** (root includes dev requirements like `pytest`/`pytest-cov` that the backend file omits). The duplication/drift risk is still valid.

4. **Bootstrap/env references are materially broken**: The report mentions drift between `.env.example` and `backend/example.env`. On current `main`, `backend/example.env` **does not exist**, yet `backend/scripts/setup.sh` still references it and copies it. This is a **real onboarding break**, not just drift.

5. **README vs webhook behavior**: The report’s claim that the README “delta sync with cursors” doesn’t match webhook behavior is still accurate: `backend/app/routes/plaid_webhook.py` uses `account_logic.refresh_data_for_plaid_account(...)` (legacy), while `backend/app/services/plaid_sync.py` exists as the cursor-based sync implementation.

---

CONTINUED:

Delta-based sync exists but is not the primary path:

The repo includes a well-structured services/plaid_sync.py that implements cursor-based transactions/sync and bulk-ish atomic batches, which is more scalable than repeatedly pulling long lookback windows.

<!-- COMMENT: Confirmed on main: services/plaid_sync.py exists and implements cursor-based sync. -->

Aligning the webhook/refresh path with this service is a major “high leverage” opportunity.

<!-- COMMENT: Confirmed on main: backend/app/routes/plaid_webhook.py currently triggers account_logic.refresh_data_for_plaid_account (legacy /transactions/get path), not plaid_sync.py. -->

Strengths, weaknesses, and high-leverage refactors
Strengths (already solid)

Strong CI discipline (format, lint, tests, validate-dev, docs checks).
Clear blueprint registration list and “dead code awareness” with an internal repository map.

Thoughtful operational components like the Cloudflare webhook forwarder and webhook signature verification.

Non-trivial data-serving improvements: pagination, filtering, and (small) caching; optional running-balance window function.

A real, implementation-grade delta sync service is present (services/plaid_sync.py).

<!-- COMMENT: Confirmed on main. -->

Weaknesses (scalability/maintenance risks)

Inconsistent env and onboarding story (docs vs scripts vs code), including an apparent break in backend/scripts/setup.sh (FLASK_APP="run:app" but backend/run.py defines no app).

<!-- COMMENT: Confirmed on main. Additionally, backend/scripts/setup.sh references backend/example.env which does not exist on main, so the script is broken even earlier in the flow. -->

Token leakage in logs during Plaid token exchange.

<!-- COMMENT: Confirmed on main: access token logged at INFO in plaid token exchange route. -->

Duplicate ingestion paths (legacy /transactions/get vs delta transactions/sync), which also creates documentation ambiguity.

<!-- COMMENT: Confirmed on main: both paths exist; README claims cursor-based sync, webhook currently uses legacy refresh. -->

Dead/legacy modules remain in-tree and increase cognitive load (FastAPI route module, missing Fidelity service route, ad-hoc plaid transfer PoC).

<!-- COMMENT: Likely outdated as written: those specific example files (product_transactions.py, fidelity.py, plaid_transfer.py) do not appear to exist on main today, though docs/maps may still reference them and the “dead code awareness” concept remains relevant. -->

Pre-commit config is not portable due to a hard-coded interpreter path.

<!-- COMMENT: Confirmed on main: .pre-commit-config.yaml pins a user-specific interpreter path. -->

High-leverage refactors (small-ish changes with big payoff)

Replace webhook-triggered ingestion and manual refresh flows to use services/plaid_sync.py instead of long-range /transactions/get, reducing load and aligning implementation with README claims.

<!-- COMMENT: Still valid on main given current webhook dispatch. -->

Remove or archive dead modules (product_transactions.py, fidelity.py, plaid_transfer.py) so “what runs” matches “what’s in tree.”

<!-- COMMENT: Likely outdated as written: these specific files do not appear to exist on main today; if you want to pursue this, first reconcile docs/maps that still reference them and/or identify other current dead modules. -->

Fix the backend setup script to point Flask CLI at the correct application entrypoint (factory) and normalize env template references to one canonical pattern.

<!-- COMMENT: Confirmed on main: setup.sh FLASK_APP points to run:app but run.py has no app; also setup.sh copies backend/example.env which does not exist on main. -->

Replace the pre-commit interpreter pin with a generic python3/python approach and/or use language_version: python3.

<!-- COMMENT: Confirmed needed on main. -->

Documentation and truth alignment
Where docs match reality
README correctly describes the core architecture (Flask API + Vue client + Postgres via SQLAlchemy/Alembic).
The repo maintains a real docs index and a structured doc tree that points to high-traffic backend references.
The Cloudflare worker for webhooks aligns with README guidance about using a worker domain for webhook routing.

Where docs diverge from code
README claims webhook events “trigger per-account sync” via Plaid’s delta-based transactions sync with cursors.

But the webhook handler currently triggers account_logic.refresh_data_for_plaid_account, which uses /transactions/get and a long lookback window (not the cursor-based sync service).

<!-- COMMENT: Confirmed on main: plaid_webhook.py calls account_logic.refresh_data_for_plaid_account. -->

The “Environment Reference” claims the frontend typically does not require a .env beyond Vite defaults.

Yet the repo includes frontend/.env.example with required-ish settings like VITE_APP_API_BASE_URL, and UI flows appear to rely on VITE_USER_ID_PLAID and other values.

<!-- COMMENT: Confirmed that frontend/.env.example exists and contains these fields. Whether UI “relies” on them depends on runtime configuration, but the drift between docs guidance and presence of the template is real. -->

The organizational plan suggests pre-commit hooks are a “future enhancement,” but an actual .pre-commit-config.yaml exists.

<!-- COMMENT: Confirmed on main: .pre-commit-config.yaml exists; doc guidance may be stale. -->

Backend onboarding scripts and docs disagree about the env template source:

Docs and scripts reference backend/example.env (copy to .env).

<!-- COMMENT: Confirmed: scripts reference backend/example.env; however backend/example.env does not exist on main, so this is a breaking mismatch, not just disagreement. -->

Organization guidance references backend/.env.example.
The backend setup script appears broken for Flask migrations: it sets FLASK_APP="run:app", but backend/run.py does not define an app symbol.

<!-- COMMENT: Confirmed on main. -->

Planned development features and “what’s next” signals
The repo contains explicit TODO planning docs (including deprecated ones that point to newer consolidated TODOs):

docs/maintenance/todo.md is marked deprecated and points to a consolidated frontend TODO document; it includes UI improvements (dashboard styling, dropdown/fuzzy search, category tree filtering, pagination, “Integrate the Plaid removal endpoint upon deletion,” etc.).

The repository map identifies “needs follow-up” directories (scripts, tools, workers) and explicitly calls out legacy backend route modules for archival.

Doc Fix List with concrete edits
README: adjust “delta-based Transactions Sync” section to reflect the current implementation, or update implementation to match README (recommended). At minimum, clarify whether /api/webhooks/plaid triggers account_logic.refresh_data_for_plaid_account (transactions/get) or services/plaid_sync.sync_account_transactions (transactions/sync).

<!-- COMMENT: Confirmed mismatch exists on main. -->

docs/ENVIRONMENT_REFERENCE.md: correct frontend .env guidance and explicitly document frontend/.env.example fields (including whether PHONE_NBR is actually needed).

docs/ENVIRONMENT_REFERENCE.md and README Quickstart: reconcile “copy backend/example.env” vs “copy backend/.env.example” and make one canonical.

<!-- COMMENT: Confirmed urgent: backend/example.env does not exist on main but is referenced by scripts/docs. -->

backend/scripts/setup.sh: fix Flask CLI invocation to reference the app factory correctly (and document it).

<!-- COMMENT: Confirmed needed on main. -->

ORGANIZATION.md: update the “Recommended Additions” pre-commit section to reflect that pre-commit already exists; replace the sample block with “how to install/use pre-commit in this repo.”
docs/maps/repository_map.md header date: the title says “(2025-02-12)” while the file has been modified much later; update the date in the header or replace with “Last reviewed: …” to keep trust.

Risk and priority matrix
Rubric used:

Impact: user value / correctness / security / maintainability
Effort: S (≤1 day), M (2–5 days), L (≥1–2 weeks)
Risk: likelihood × blast radius
Dependencies: what must be done first or what is blocked
Priority-ordered work items (15 total)

Stop logging Plaid access tokens in plaintext
Impact: Very high (credential leak)
Effort: S
Risk: Very high
Dependencies: none
Evidence: access token is logged at INFO level in Plaid token exchange route.

<!-- COMMENT: Confirmed on main. -->

Fix backend bootstrap migration script (backend/scripts/setup.sh)
Impact: High (onboarding + DB migrations)
Effort: S
Risk: High (script likely fails)
Dependencies: decide canonical Flask app entrypoint
Evidence: script sets FLASK_APP="run:app" but backend/run.py defines no app.

<!-- COMMENT: Confirmed on main; additionally script references backend/example.env which does not exist on main. -->

Unify env template strategy (one source of truth)
Impact: High (security + DX)
Effort: M
Risk: High (secrets drift, incorrect config)
Dependencies: decide whether to keep example.env or .env.example
Evidence: docs + scripts use backend/example.env while org plan describes .env.example.

<!-- COMMENT: Confirmed; and backend/example.env is missing on main, so this is immediately blocking. -->

Align Plaid “transactions sync” implementation with README
Impact: High (correctness, scalability, user expectations)
Effort: M
Risk: High (data correctness + regressions)
Dependencies: design decision: adopt services/plaid_sync.py as canonical ingestion path
Evidence: README claims cursor-based delta sync; webhook triggers refresh, but current webhook path calls account_logic.refresh_data_for_plaid_account which uses /transactions/get.

<!-- COMMENT: Confirmed on main: README says delta sync; plaid_webhook.py uses account_logic.refresh_data_for_plaid_account. -->

Archive or delete dead/legacy route modules
Impact: Medium (maintainability, security surface)
Effort: S–M
Risk: Medium (accidental reactivation, confusion)
Dependencies: confirm no imports/usage
Evidence: FastAPI route file, missing service route file, and ad-hoc transfer PoC are not registered in the app factory.

<!-- COMMENT: Likely outdated as written: those specific example files do not appear to exist on main. Validate current dead modules (or doc-map drift) before actioning. -->

Make .pre-commit-config.yaml portable
Impact: Medium (team workflow, CI parity)
Effort: S
Risk: Medium
Dependencies: none
Evidence: hard-coded interpreter path in pre-commit config.

<!-- COMMENT: Confirmed on main. -->

Consolidate dependency files (choose root or backend requirements.txt)
Impact: Medium (DX + CI correctness)
Effort: S
Risk: Medium
Dependencies: update CI + docs accordingly
Evidence: duplicate identical requirements in root and backend.

<!-- COMMENT: Duplication exists on main; “identical” is outdated (root includes dev deps like pytest/pytest-cov that backend/requirements.txt omits). -->

Harden CORS and define deployment security model
Impact: High (security if deployed publicly)
Effort: M
Risk: High
Dependencies: decide whether to introduce auth/session in Phase 1 vs Phase 2
Evidence: CORS(app) enabled globally; frontend uses no auth headers; user scoping often client-provided.

Introduce a unified request validation layer for key API surfaces
Impact: Medium–High (stability, correctness)
Effort: M
Risk: Medium
Dependencies: choose library/approach (Pydantic, Marshmallow, dataclasses + manual)
Evidence: validation is currently ad-hoc and duplicated in routes.
Reduce ingestion cost by removing “680 day lookback by default”
Impact: Medium–High (rate limiting, latency)
Effort: M
Risk: Medium
Dependencies: move to cursor-based deltas or configurable lookback
Evidence: lookback constant in refresh_data_for_plaid_account.
Optimize transaction upsert patterns to avoid per-row DB lookups
Impact: Medium (performance)
Effort: M
Risk: Medium
Dependencies: schema constraints/unique indexes, decide upsert strategy
Evidence: per-transaction Transaction.query.filter_by(...).first() pattern inside loops in both ingestion paths.

Normalize “transaction update” endpoints (remove duplication, keep one canonical behavior)
Impact: Medium
Effort: S–M
Risk: Low–Medium
Dependencies: confirm frontend usage
Evidence: both /update and /user_modify/update exist with overlapping logic.

Clarify/resolve “fidelity_worker” story
Impact: Medium (deployment, dead services)
Effort: M
Risk: Medium
Dependencies: determine whether Fidelity integration is still wanted
Evidence: docker-compose defines a fidelity worker, but in-tree route references a missing service and isn’t registered.

<!-- COMMENT: Confirmed that docker-compose references a fidelity_worker build context that is missing on main. The “in-tree route references a missing service” portion may be outdated if the referenced route file no longer exists. -->

Finalize frontend UX backlog for Dashboard/Accounts flows
Impact: Medium (user value)
Effort: L
Risk: Low–Medium
Dependencies: API stability + data model decisions
Evidence: deprecated TODO doc enumerates needed UI fixes and explicitly calls out integrating deletion with the Plaid removal endpoint.
Reconcile docs across ENV / organization / repo map (single “truth path”)
Impact: Medium
Effort: S–M
Risk: Low
Dependencies: items 2–3 (so docs match fixed implementation)
Evidence: mismatches across docs.

Concrete phased roadmap with milestones and acceptance criteria
Phase 0: Repo hygiene and safety
Goal: make the repo safe to run locally, safe to contribute to, and safe to deploy accidentally.

Milestone: Secrets and logging safety

Likely touched: backend/app/routes/plaid_transactions.py, .gitignore, frontend/.env.example, docs.
Steps:
Remove or redact sensitive-token output in Plaid token exchange route logs; keep logging to item_id only.

<!-- COMMENT: Confirmed relevant: token logging exists on main. -->

Add a test that asserts no log message includes an access token pattern (simple regex-based unit test around “exchange_public_token” endpoint).
Confirm .env templates do not contain “real-looking” secrets; keep placeholders obviously fake (e.g., PHONE_NBR=+10000000000 could be replaced by +19999999999 plus a comment that it’s a dummy).
Definition of done:
No route logs access_token values.
Tests and CI pass.
Milestone: Bootstrap correctness

Likely touched: backend/scripts/setup.sh, docs/ENVIRONMENT_REFERENCE.md, README.md.
Steps:
Fix Flask CLI invocation in setup script: point at the factory (--app backend.run:create_app) or restructure backend/run.py to expose app = create_app() for CLI compatibility (choose one; keep consistent).
Update docs to match.
Definition of done:
Running bash backend/scripts/setup.sh successfully runs migrations on a clean environment using the repo’s prescribed prerequisites.

<!-- COMMENT: As of main today, this will fail because backend/example.env is missing and FLASK_APP points to run:app without an app symbol. -->

Milestone: Tooling portability

Likely touched: .pre-commit-config.yaml.
Steps:
Remove user-specific interpreter path; rely on python3.
Add a short contributor note on installing pre-commit and running pre-commit run --all-files.
Definition of done:
pre-commit install works on a clean environment and matches CI enforcement.
Suggested order of operations: logging safety → setup script fix → env template consolidation → pre-commit portability → docs edits.

Phase 1: Architecture stabilization
Goal: reduce duplication, clarify boundaries, and make integrations testable and maintainable.

Milestone: One canonical transactions ingestion path

Likely touched: backend/app/routes/plaid_webhook.py, backend/app/routes/plaid_transactions.py, backend/app/services/plaid_sync.py, backend/app/sql/account_logic.py, docs.
Steps:
Decide: adopt cursor-based services/plaid_sync.sync_account_transactions() as canonical ingestion, and keep /transactions/get flow as a fallback only if needed.
Update webhook handler to dispatch delta sync per account (or per item → all accounts) using cursor.

<!-- COMMENT: Confirmed needed on main to align behavior with README claims. -->

Ensure cursor persistence is correct (service already updates PlaidAccount.sync_cursor).
Definition of done:
README “Sync & Webhooks” section accurately matches implementation.
Basic integration tests verify webhook pathways call the expected service layer.
Milestone: Normalize routes/services/errors

Likely touched: key route modules (transactions.py, plaid_transactions.py, plaid_webhook.py) and shared utility module.
Steps:
Introduce a shared error response helper (e.g., api_error(code, message, http_status)).
Standardize validation/errors for key endpoints (dates, pagination, missing ids).
Remove duplicate transaction update endpoint or make one route call the other.
Definition of done:
80%+ of routes use the shared error helper and consistent response envelopes.
Phase 2: Feature completion
Goal: finish “nearly done” user-facing features with the least architectural risk.

Candidates that appear “close” based on existing APIs and TODOs:

Account deletion that fully revokes Plaid items: The backend provides a delete endpoint that removes Plaid items and deletes linked accounts; the frontend TODO explicitly calls for integrating this on the Accounts screen.

Tags + rules workflow: Transaction update supports tags and an optional “save as rule” behavior; front-end polish and consistency remain.
Milestone: Account deletion UX

Likely touched: frontend/src/services/api.js plus Accounts view/components; backend route already exists.
Steps:
Wire “Delete account” UI to call backend delete endpoint.
Confirm behavior for linked accounts within an item (backend attempts to delete linked accounts).
Definition of done:
Deleting a linked account removes the Plaid item and all linked accounts, and the UI refreshes correctly.
Phase 3: UX and performance
Goal: reduce latency, improve perceived performance, and harden high-traffic endpoints.

Milestone: Transaction list performance + pagination UX

Likely touched: backend/app/sql/account_logic.py, backend/app/routes/transactions.py, frontend list components.
Steps:
Add server-side constraints: max page_size, enforce reasonable bounds.
Consider “estimated total” or optional include_total=false to skip costly counts for large queries.
Improve caching strategy (move from in-process dict to Redis or disable in multi-process production).
Definition of done:
Transactions endpoint stays within target latency under typical page sizes for a large dataset.
Milestone: Frontend fetch + error handling

Likely touched: frontend/src/services/api.js.
Steps:
Add Axios interceptors for common error shapes and user-friendly toast messaging.
Centralize baseURL and environment behavior.
Definition of done:
Consistent error reporting and fewer “silent failures” in UI.
Agentic implementation plan (Codex-ready, PR-sized)
Branch strategy and PR sequence

Branch naming: chore/*, fix/*, refactor/*, feat/*, docs/*
Sequence: land “safety + bootstrap” first, then refactor surfaces with test scaffolding, then features, then perf.
PR-sized tasks (each ~1–3 hours)

PR 1: Remove access token logging

Objective: eliminate sensitive token leakage.
Files to inspect/change first: backend/app/routes/plaid_transactions.py (token exchange logs).
Constraints: no API shape changes.
Validation:
pytest -q
Manually hit /api/plaid/transactions/exchange_public_token in dev and inspect logs.
Rollback: revert logging lines only.
PR 2: Fix backend/scripts/setup.sh Flask app reference

Objective: make migrations run reliably.
Files: backend/scripts/setup.sh, possibly docs (docs/ENVIRONMENT_REFERENCE.md) for command examples.

Constraints: keep existing dev flow (python backend/run.py) working.
Validation:
Run the script in a clean environment.
Confirm flask db upgrade succeeds.
Rollback: restore prior script, but document known break.
PR 3: Make pre-commit portable

Objective: remove hard-coded interpreter path.
Files: .pre-commit-config.yaml.
Constraints: keep hooks behavior unchanged.
Validation:
pre-commit run --all-files
CI Format, Test, and Validate remains green.
Rollback: revert config.
PR 4: Consolidate requirements file usage (pick one canonical)

Objective: remove duplication and drift hazard.
Files: requirements.txt, backend/requirements.txt, CI workflow format_and_test.yaml, docs.

<!-- COMMENT: On main, root requirements.txt includes dev deps not present in backend/requirements.txt; consolidation is still valid but not a pure dedupe of identical files. -->

Constraints: keep install commands simple.
Validation: CI + local pip install -r ... + pytest.
Rollback: restore duplicated file and update docs accordingly.
PR 5: Archive dead backend route modules

Objective: reduce confusion/security surface.
Files: backend/app/routes/product_transactions.py, backend/app/routes/fidelity.py, backend/app/routes/plaid_transfer.py; update repo map/docs.

<!-- COMMENT: Likely outdated as written: these files do not appear to exist on main today, so this PR would need to be reframed as “reconcile docs/maps and remove stale references” or target different current dead modules. -->

Constraints: do not break imports; confirm not registered in app factory.
Validation:
pytest
Ensure create_app() still imports all registered modules.
Rollback: move files back from archive.
PR 6: Align webhook transaction refresh with delta sync service (scaffold)

Objective: make README claim true or explicitly update docs.
Files: backend/app/routes/plaid_webhook.py, backend/app/services/plaid_sync.py, docs/README sync section.

<!-- COMMENT: Confirmed on main: webhook currently uses legacy refresh; README claims cursor sync. -->

Constraints: keep current behavior behind a feature flag initially (USE_PLAID_SYNC_CURSOR=true) to reduce risk.
Validation:
Unit test for webhook dispatch path.
Manual dev test with a mocked Plaid client.
Rollback: toggle off feature flag; restore old dispatch.
PR 7: Add request-shape validation for top endpoints

Objective: consistent validation and stable error responses.
Files: backend/app/routes/transactions.py, backend/app/routes/plaid_transactions.py, shared backend/app/utils/ module.
Constraints: do not change response envelopes yet.
Validation: existing tests + add 2–3 new tests for invalid params.
PR 8: Frontend deletion integration (Accounts)

Objective: implement “Plaid removal endpoint upon deletion” UX.
Files: frontend/src/services/api.js, Accounts view/components, any confirmation modal, and backend deletion endpoint contract.

Constraints: no backend changes unless required for UI correctness.
Validation:
Manual: link account → delete → verify account list refreshes.
Frontend unit/component tests where feasible.
Rollback: hide feature behind UI flag.
Review checklist (apply to every PR)

Style: Black/isort/Ruff clean; frontend eslint/prettier clean.

Tests: pytest passes; if frontend touched, run npm run test / component tests as applicable.
Security: no secrets/logging leaks; .env templates remain placeholders only.
Docs: update README/docs if you changed behavior or bootstrap flows.
Recommended automation helpers

Keep CI workflow as the “single gate” (format + tests + validate-dev + docs).
Use pre-commit locally after portability fix to match CI.
Expand unit tests in the pattern used by existing route tests (module stubs + monkeypatch) until deeper DI refactors land.

<!-- BOTTOM COMMENTS (rewritten, consolidated)
1) Dead/legacy module examples: The report references specific legacy route files (product_transactions.py, fidelity.py, plaid_transfer.py) as present “in-tree.” On current main, those specific files do not appear to exist. If this work item is still desired, re-scope it to (a) reconciling docs/maps that still list them and/or (b) identifying other current dead code paths.
2) chromadb directory: Earlier in the report, chromadb is listed as a top-level stale directory. On current main, chromadb/ does not appear to exist at repo root; treat that as an outdated directory-level claim.
3) Requirements duplication: Both requirements.txt files exist, but they are not identical on current main (root includes dev deps like pytest/pytest-cov that backend/requirements.txt omits). The “drift risk” point still stands; the “identical” claim is outdated.
4) Bootstrap is broken in two independent ways: backend/scripts/setup.sh references backend/example.env (missing on main) and also sets FLASK_APP="run:app" even though backend/run.py does not define a module-level app. This is an onboarding blocker beyond “drift.”
5) Plaid sync mismatch: Confirmed on current main—README claims cursor-based delta sync and per-account webhook-triggered sync, but backend/app/routes/plaid_webhook.py dispatches to account_logic.refresh_data_for_plaid_account (legacy /transactions/get). services/plaid_sync.py exists and is the likely target for alignment. -->
