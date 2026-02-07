# pyNance State of the Repo and Implementation Roadmap

This document organizes current repo observations, risks, and a prioritized roadmap. It preserves the original context while making the content scannable and action-oriented.

---

## 1. Repo Map (Evidence + Boundary Notes)

pyNance is a monorepo: **Flask API** (`backend/`), **Vue 3/Vite SPA** (`frontend/`), and extensive documentation under `docs/`.

### Top-Level Directories (Intended Purpose)

- `backend/` — Flask API + CLI + Alembic migrations (canonical server runtime)
- `frontend/` — Vue 3/Vite app (package name `dashvue`)
- `docs/` — documentation tree, roadmaps, audits, environment references
- `scripts/` — repo automation and validation scripts
- `tests/` — pytest suite (route/service tests; heavy stubbing)
- `workers/` — Cloudflare Worker forwarding Plaid webhooks
- `tools/` — one-off utilities (e.g., symbol mapping)

### Backend vs Frontend Boundary

- Boundary is HTTP.
- Frontend Axios defaults to `VITE_APP_API_BASE_URL` or `/api` and calls routes like `/accounts/get_accounts`, `/transactions/get_transactions`, `/charts/*`, `/dashboard/*`.
- Backend registers blueprints in `backend/app/__init__.py`; anything not imported and registered is effectively dead code.

### Config and Env Templates (Drift / Risk)

Observed mismatches:

- Templates exist for backend and frontend (`backend/.env.example`, `frontend/.env.example`).
- Frontend `.env.example` includes PII-shaped fields (`PHONE_NBR`, `VITE_USER_ID_PLAID`), increasing risk of accidental sensitive data leakage.
- Docs and tooling still refer to `backend/example.env` as the canonical template.

**Comments:**

- As of current `main`, `backend/example.env` does **not exist**. Scripts and docs referencing it will break onboarding.
- `backend/scripts/setup.sh` copies from `backend/example.env`, which currently fails.

### Scripts, Utilities, Migrations

- `backend/scripts/setup.sh` starts Postgres (via docker-compose) and runs migrations.
- `backend/docker-compose.yml` defines a `fidelity_worker` service; build context appears missing.
- Repo-level `scripts/validate-dev.sh` is used in CI for lint/test/docs checks.
- Flask CLI tools exist for import/backfill/sync operations.

**Comments:**

- `fidelity_worker` build context appears missing on `main` (compose mismatch).

### Inconsistencies / Dead or Unclear Areas

Repo documentation calls out stale/unregistered modules. Examples **in the original report** included:

- `backend/app/routes/product_transactions.py` (FastAPI-style, unregistered)
- `backend/app/routes/fidelity.py` (missing service dependency)
- `backend/app/routes/plaid_transfer.py` (standalone Flask app, unregistered)

**Comments:**

- These specific files **do not appear to exist** on current `main`. The *concept* of stale references still matters, but examples must be refreshed before actioning.

### Requirements Duplication

- Root `requirements.txt` and `backend/requirements.txt` both exist.

**Comment:**

- They are **not identical** on current `main` (root includes dev deps). Drift risk remains.

---

## 2. Architecture & Data Flow Assessment

### Structure & Modularity

- **Routes**: Flask blueprints under `backend/app/routes/*`, registered in `backend/app/__init__.py`.
- **SQL logic**: `backend/app/sql/*` (mix of business rules + persistence logic).
- **Helpers**: external API helpers under `backend/app/helpers/*`.
- **Services**: cohesive flows, notably `backend/app/services/plaid_sync.py` for cursor-based Plaid sync.

**Comment:**

- `services/plaid_sync.py` exists and implements cursor-based sync (confirmed on `main`).

### Consistency: Logging, Validation, Types

Strengths:

- Strong CI checks (format/lint/tests/docs).
- Defensive and typed code in some services (e.g., plaid sync).
- AST-based tests to guard against invalid model fields.

Weaknesses:

- `.pre-commit-config.yaml` pins a user-specific interpreter path.
- Docs and code disagree on env truth (`FLASK_ENV` vs ENV-only approach).
- Validation is ad-hoc; no unified schema layer.

### Coupling / Duplication

- Two Plaid ingestion paths:
  - Legacy `/transactions/get` via `account_logic.refresh_data_for_plaid_account`.
  - Cursor-based `/transactions/sync` via `services/plaid_sync.py`.
- Overlapping transaction update endpoints: `/update` and `/user_modify/update`.
- Duplicate requirements files.

---

## 3. End-to-End Data Flow (Transactions)

### Ingestion → Normalization → Persistence → UI

1. **Frontend** triggers Plaid link and fetches accounts/transactions.
2. **Backend** persists Plaid items/accounts, upserts Accounts.
3. **Normalization** handles balance, amount, categories, merchant metadata.
4. **Persistence** stores transactions + auxiliary Plaid metadata.
5. **Serving** via `/api/transactions/get_transactions` with pagination and light caching.

### Webhooks

- Cloudflare Worker forwards Plaid webhooks to `/api/webhooks/plaid`.
- Backend validates `Plaid-Signature`, logs events, persists to `PlaidWebhookLog`.
- On `TRANSACTIONS` webhook events, it triggers legacy refresh path.

**Comment:**

- Webhooks currently call `account_logic.refresh_data_for_plaid_account`, **not** the cursor-based sync service.

---

## 4. Reliability, Security, Performance

### Reliability Posture

- CI gates are strong.
- Tests use module stubbing; import-time dependencies make testing harder.

### Security Risks (High Signal)

- No clear auth boundary; user scoping often client-provided.
- Global CORS is enabled (`CORS(app)`), amplifying exposure risk.
- Plaid access tokens are logged at INFO level during token exchange.
- Env templates include PII-shaped fields (e.g., `PHONE_NBR`).

**Comments:**

- Token logging is confirmed on `main`.

### Performance Hotspots

- Legacy ingestion performs per-transaction DB lookups in loops.
- Large default lookback window (680 days) increases load.
- Pagination counts can be expensive for large datasets.
- Cache is in-process only (TTL 90s, pages ≤5).

---

## 5. Bottom-Line Corrections / Outdated Claims

These were explicitly noted in the original report and should be treated as corrections:

1. **Dead/legacy modules**: `product_transactions.py`, `fidelity.py`, `plaid_transfer.py` are **not present** on current `main`. Re-scope to current dead code or update docs that reference them.
2. **`chromadb/` directory**: No longer exists at repo root.
3. **Requirements files**: Both exist but are **not identical** on `main`.
4. **Bootstrap script**: `backend/scripts/setup.sh` is broken in two ways:
   - References missing `backend/example.env`.
   - Sets `FLASK_APP="run:app"` though `backend/run.py` has no module-level `app`.
5. **Plaid sync mismatch**: README claims cursor-based delta sync, but webhook path still uses legacy `/transactions/get` route.

---

## 6. Priority Work Items (Risk/Impact/Effort)

### Rubric

- **Impact**: user value / correctness / security / maintainability
- **Effort**: S (≤1 day), M (2–5 days), L (≥1–2 weeks)
- **Risk**: likelihood × blast radius

### Priority-Ordered List (15 items)

1. **Stop logging Plaid access tokens**
   - Impact: Very high | Effort: S | Risk: Very high
   - Evidence: Token logged at INFO level in exchange route.

2. **Fix backend bootstrap migrations** (`backend/scripts/setup.sh`)
   - Impact: High | Effort: S | Risk: High
   - Evidence: `FLASK_APP` points to missing `app` symbol; `backend/example.env` missing.

3. **Unify env template strategy**
   - Impact: High | Effort: M | Risk: High
   - Evidence: docs and scripts refer to missing template.

4. **Align Plaid sync with README**
   - Impact: High | Effort: M | Risk: High
   - Evidence: webhook uses legacy refresh; cursor-based sync exists.

5. **Archive or delete dead/legacy modules**
   - Impact: Medium | Effort: S–M | Risk: Medium
   - Evidence: repo map still references dead modules; confirm current state first.

6. **Make pre-commit portable**
   - Impact: Medium | Effort: S | Risk: Medium
   - Evidence: user-specific interpreter path.

7. **Consolidate dependency files**
   - Impact: Medium | Effort: S | Risk: Medium
   - Evidence: dual requirements with drift.

8. **Harden CORS / define auth model**
   - Impact: High | Effort: M | Risk: High
   - Evidence: global CORS; no auth.

9. **Introduce request validation layer**
   - Impact: Medium–High | Effort: M | Risk: Medium
   - Evidence: ad-hoc validation.

10. **Reduce 680-day lookback default**
    - Impact: Medium–High | Effort: M | Risk: Medium
    - Evidence: large default lookback in legacy ingestion.

11. **Optimize transaction upsert patterns**
    - Impact: Medium | Effort: M | Risk: Medium
    - Evidence: per-row DB queries in ingestion.

12. **Normalize transaction update endpoints**
    - Impact: Medium | Effort: S–M | Risk: Low–Medium
    - Evidence: duplicate endpoints.

13. **Clarify fidelity_worker story**
    - Impact: Medium | Effort: M | Risk: Medium
    - Evidence: docker-compose references missing build context.

14. **Finalize frontend UX backlog (Dashboard/Accounts)**
    - Impact: Medium | Effort: L | Risk: Low–Medium
    - Evidence: TODO docs list UI improvements.

15. **Reconcile docs across ENV / organization / repo map**
    - Impact: Medium | Effort: S–M | Risk: Low
    - Evidence: mismatches between docs and code.

---

## 7. Phased Roadmap (Milestones + DoD)

### Phase 0: Repo Hygiene & Safety

**Milestone: Secrets & Logging**

- Remove access-token logging in Plaid token exchange.
- Add test to assert logs do not emit token patterns.
- Clean env templates of PII-shaped placeholders.

**Definition of Done:**

- No token logs; tests pass; templates are safe.

**Milestone: Bootstrap Correctness**

- Fix `backend/scripts/setup.sh` to reference the correct app factory.
- Update docs/README to match the canonical env template.

**Definition of Done:**

- `backend/scripts/setup.sh` runs migrations successfully on a clean environment.

**Milestone: Tooling Portability**

- Remove user-specific interpreter path from `.pre-commit-config.yaml`.
- Add contributor note on installing/running pre-commit.

---

### Phase 1: Architecture Stabilization

**Milestone: One Canonical Transactions Ingestion Path**

- Decide to adopt cursor-based `services/plaid_sync.py` as canonical.
- Update webhook handler to dispatch through cursor-based sync.
- Keep legacy path only as fallback or remove after confidence.

**Definition of Done:**

- README matches implementation; integration tests cover webhook path.

**Milestone: Normalize Routes/Errors**

- Shared error response helper.
- Standardize validation on core endpoints.
- Remove or fold duplicate transaction update endpoint.

---

### Phase 2: Feature Completion

**Milestone: Account Deletion UX**

- Wire frontend delete flow to backend Plaid removal endpoint.
- Ensure UI refresh and linked-account behavior matches backend.

**Definition of Done:**

- Deleting a linked account removes the Plaid item; UI reflects new state.

**Milestone: Tags + Rules UX Polish**

- Align frontend with transaction update + rule creation behavior.

---

### Phase 3: UX & Performance

**Milestone: Transactions Performance**

- Enforce server-side page size bounds.
- Consider optional “no total count” for large queries.
- Improve caching strategy (Redis or disable in multi-process).

**Milestone: Frontend Fetch + Error Handling**

- Centralize Axios error handling + baseURL config.

---

## 8. PR-Sized Implementation Plan

Suggested sequence:

1. Remove access token logging.
2. Fix `backend/scripts/setup.sh` + env template references.
3. Make pre-commit portable.
4. Consolidate requirements files.
5. Reconcile docs/maps for dead modules (or archive current dead code after confirmation).
6. Align webhook ingestion with cursor-based sync (feature-flagged).
7. Add request validation for top endpoints.
8. Frontend account deletion integration.

Each PR should include:

- Tests executed (or explicitly skipped).
- Docs updated when behavior changes.
- Security review note (token handling, env templates).

---

## 9. Review Checklist (Apply to Every PR)

- Format/lint/test gates green.
- No sensitive data logged or committed.
- Docs updated if behavior or bootstrap flows change.
- Frontend changes include screenshots for UI-visible updates.
