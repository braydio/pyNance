# =============================================================================
# Stage 1 — Build the Vue 3 frontend
# =============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# =============================================================================
# Stage 2 — Python backend with gunicorn
# =============================================================================
FROM python:3.12-slim

WORKDIR /app

# ── System dependencies ──────────────────────────────────────────
# gcc is needed by some pip packages at install time (not at runtime).
# Clean up after ourselves to keep the image lean.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ──────────────────────────────────────────
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ── Application code ─────────────────────────────────────────────
COPY backend/ ./backend/

# Built frontend – Flask expects it at <repo-root>/frontend/dist
# resolved from backend/app/config/constants.py
COPY --from=frontend-builder /build/dist ./frontend/dist/

# ── Entrypoint ───────────────────────────────────────────────────
COPY backend/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/docker-entrypoint.sh"]
