# Repository Guidelines

## Project Structure & Module Organization

- `frontend/src/` holds the Vue 3 app (script-setup components, stores, assets, and routes).
- `frontend/src/components/` is the shared UI surface; keep components cohesive and scoped.
- `frontend/src/views/` contains route-level pages and layouts.
- Frontend documentation lives in `frontend/docs/`; update or add docs there when changing UI behavior.
- Cross-functional or architecture docs remain under `docs/frontend/` when they need to be referenced outside the frontend team.

## Build, Test, and Development Commands

- `cd frontend && npm run dev` – starts the Vite dev server.
- `cd frontend && npm run build` – produces the production build.
- `cd frontend && npm run lint` – runs ESLint for the frontend.
- `cd frontend && npm run test:unit` – runs Cypress component tests.
- `cd frontend && npm run test:e2e` – runs Cypress end-to-end tests.

## Coding Style & Naming Conventions

- Vue components use `<script setup>` and scoped styles unless a file is explicitly global.
- Favor CSS variables from `frontend/src/styles/theme.css` for colors and surfaces.
- Avoid hardcoded colors and spacing; use theme variables and Tailwind utilities instead.
- Keep component names `PascalCase` and file names consistent with the component name.

## Testing Guidelines

- Add or update Cypress component tests for new UI logic.
- Add end-to-end coverage for new flows that touch routes or critical user actions.
- Mention any skipped UI tests explicitly in PR notes.

## Commit & Pull Request Guidelines

- Follow Conventional Commits with a focused scope (for example, `feat(transactions): refine inline editing hints`).
- PRs should summarize UI impact, call out affected screens, and include screenshots when visuals change.

## Security & Configuration Tips

- Never commit secrets; use local `.env` files for API endpoints or feature flags.
- Keep mock data and fixtures in test directories only.
