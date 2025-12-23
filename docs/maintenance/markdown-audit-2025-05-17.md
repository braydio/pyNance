# Markdown File Audit (May 17, 2025)

Purpose: classify every tracked Markdown file by recommended action (acceptable, needs content update, relocate, or deprecate) to align documentation with current structure.

## Legend

- **Keep**: location/content acceptable.
- **Update**: content needs refresh or verification.
- **Move**: relocate to a more relevant directory (content otherwise fine).
- **Deprecate**: retire or merge; note existing replacements where known.

## Root-Level Files

- `ACCOUNT_SNAPSHOT_FIXES.md` — Move to `docs/maintenance/` and confirm whether tasks are still open; document is a temporary checklist intended for removal once completed. **Move + Update**
- `AGENTS.md` — Keep at root; active contributor guidance referenced by automation. **Keep**
- `CONTRIBUTING.md` — Keep; primary contribution standards. **Keep**
- `DATABASE_OVERVIEW.md` — Relocate under `docs/backend/` (or `docs/architecture/`) to live with database design notes; refresh against current models. **Move + Update**
- `ORGANIZATION.md` — Move to `docs/process/`; strategic repo/process plan rather than root reference. **Move**
- `POSTGRE_CHEAT_SHEET.md` — Move to `docs/backend/` alongside other database docs. **Move**
- `README.md` — Keep; main entry point. **Keep**
- `SQL_DATABASE_CHANGES.md` — Move to `docs/backend/` and polish incomplete sentences for clarity. **Move + Update**

## Backend (non-docs) Directory

- `backend/AGENTS.md` — Keep; scoped contributor rules. **Keep**
- `backend/app/routes/CHARTS_CAT_BREAKDOWN.md` — Route-specific reference is in `backend/app/routes`; location matches scope. **Keep**
- `backend/app/services/FORECAST_RECURRING_ROADMAP.md` — Service roadmap fits services context. **Keep**
- `backend/app/static/README.md` — Static assets README fits location. **Keep**

## Backend Documentation (`docs/backend/...`)

- `docs/backend/cron_sync.md` — Keep.
- `docs/backend/features/transaction_rules.md` — Keep.
- `docs/backend/load_transactions.md` — Keep.
- `docs/backend/migrations/versions/*.md` (all) — Keep; belong with migration history.
- `docs/backend/run.md` — Keep.
- `docs/backend/scripts/delete_plaid_from_backup.md` — Keep.
- `docs/backend/scripts/map_component_use.md` — Keep.
- `docs/backend/postgres-migration.md` — Keep.
- `docs/backend/app/__init__.md` — Keep.
- `docs/backend/app/cli/*.md` (all) — Keep.
- `docs/backend/app/config/*.md` (all) — Keep.
- `docs/backend/app/extensions.md` — Keep.
- `docs/backend/app/helpers/*.md` (all) — Keep.
- `docs/backend/app/models.md` — Keep.
- `docs/backend/app/routes/*.md` (all) — Keep; mirror actual route modules.
- `docs/backend/app/services/*.md` (all) — Keep.
- `docs/backend/app/sql/*.md` and `docs/backend/app/sql/models/*.md` — Keep.
- `docs/backend/app/utils/*.md` — Keep.

## Core Docs (`docs/` root)

- `docs/API_REFERENCE.md` — Keep.
- `docs/BACKEND_STATUS.md` — Update to reflect current service health if stale. **Update**
- `docs/CODEX_REPORT.md` — Update or merge into `docs/process/` if still active; content appears archival. **Update/Assess**
- `docs/COMPONENTS_MIGRATION.md` — Update; migration status likely changed. **Update**
- `docs/ENVIRONMENT_REFERENCE.md` — Keep.
- `docs/PLAID_ERROR_REMEDIATION.md` — Keep.
- `docs/RAW_PAYLOAD_STORAGE.md` — Keep.
- `docs/README.md` — Keep.
- `docs/TAILWIND_VITE_STYLE_REFERENCE.md` — Keep.
- `docs/ToDoCodex.md` — Merge into `docs/frontend/Consolidated_TODO.md` and remove the legacy file. **Move + Update**
- `docs/arbit_dashboard.md` — Move to `docs/frontend/` to align with UI focus; duplicate with frontend version. **Move/Consolidate**
- `docs/arbitrage_page.md` — Move to `docs/frontend/` for UI alignment. **Move**
- `docs/backend_routing_plan.md` — Deprecated (already marked); keep as archived note or remove after confirming consumers. **Deprecate**
- `docs/category_breakdown_component_review.md` — Move to `docs/frontend/` with other component reviews. **Move**
- `docs/codex/review-and-refactor-backend-routes-and-sql-logic_1-of-3.md` — Keep; specialized codex note in codex folder. **Keep**
- `docs/dataflow/account_history_aggregation.md` — Keep.
- `docs/dataflow/investment_sync_pipeline.md` — Keep.
- `docs/dataflow/plaid_link_request_flow.md` — Keep.
- `docs/forecast/FORECAST_PURPOSE.md` — Keep.
- `docs/forecast/FORECAST_ROADMAP.md` — Keep.
- `docs/forecast/RECURRING_TRANSACTIONS.md` — Keep.
- `docs/forecast/notes.md` — Keep.
- `docs/frontend_duplicate_component_review.md` — Move into `docs/frontend/` to co-locate with component docs. **Move**
- `docs/index/INDEX.md` — Update after any relocations to keep index accurate. **Update**
- `docs/integrations/plaid_investments.md` — Keep.
- `docs/integrations/stake_cleanup.md` — Keep.
- `docs/devnotes/Dev_ForecastReference.md` — Keep.
- `docs/devnotes/Retrospective_Mapping.md` — Keep.
- `docs/architecture/arch_ux_02.md` — Keep.
- `docs/devnotes/refresh_route_reviewer.md` — Keep.
- `docs/latest/net_changes_feature.md` — Update if feature evolved. **Update**
- `docs/latest/recent_transactions_feature.md` — Update if feature evolved. **Update**
- `docs/maps/link_account_products_map.md` — Keep.
- `docs/maps/repository_map.md` — Update to reflect current structure. **Update**
- `docs/migration_plan.md` — Update if migration plans changed. **Update**
- `docs/organize/CODEX_RECC-MIGRATION.md` — Keep.
- `docs/organize/routing_refactor/*` (all) — Keep; organizing notes. **Keep**
- `docs/architecture/architecture_notes.md` — Keep.
- `docs/process/contributor-guide.md` — Keep.
- `docs/process/execution-plan.md` — Keep.
- `docs/process/github-templates.md` — Keep.
- `docs/process/legacy-migration.md` — Keep.
- `docs/process/pr-templates.md` — Keep.
- `docs/process/repo_organization.md` — Keep.
- `docs/resolved/runtime_context_fix.md` — Keep (resolved note for posterity).
- `docs/routing_refactor_2025-05-16.md` — Keep.
- `docs/tasklog_exchange_token_refactor.md` — Update with current status if refactor progressed. **Update**
- `docs/ui/planning.md` — Keep.

## Docs – Frontend Subtree

- `docs/frontend/CURRENCY_FORMAT_GUIDE.md` — Keep.
- `docs/frontend/Consolidated_TODO.md` — Update/merge with maintenance TODOs to reduce duplication. **Update**
- `docs/frontend/DAILY_NET_CHART.md` — Keep.
- `docs/frontend/DASHBOARD_MODAL_GUIDE.md` — Keep.
- `docs/frontend/INSTITUTIONS_PAGE.md` — Keep.
- `docs/frontend/INVESTMENTS_PAGE.md` — Keep.
- `docs/frontend/LoadingErrorComponents.md` — Keep.
- `docs/frontend/PHASES.md` — Keep.
- `docs/frontend/PageHeader.md` — Keep.
- `docs/frontend/PageLayout.md` — Keep.
- `docs/frontend/TAILWIND_SETUP.md` — Keep.
- `docs/frontend/THEMING_GUIDE.md` — Keep.
- `docs/frontend/accounts-component-spec.md` — Keep.
- `docs/frontend/accounts-development-plan.md` — Keep.
- `docs/frontend/arbit_dashboard.md` — Keep; consider consolidating with root copy. **Keep/Consolidate**
- `docs/frontend/component-review-tracker.md` — Keep.
- `docs/frontend/dashboard-component-spec.md` — Keep.
- `docs/frontend/phase-1-audit-details.md` — Keep.
- `docs/frontend/planning-view.md` — Keep.
- `docs/frontend/sparklines.md` — Keep.
- `docs/frontend/transactions-actions-sidebar.md` — Keep.
- `docs/frontend/transactions-ui.md` — Keep.

## Docs – Maintenance Subtree

- `docs/maintenance/claude-reference.md` — Deprecate or merge into `codex-reference`; duplicative naming. **Deprecate/Consolidate**
- `docs/maintenance/cleanup_checklist.md` — Keep.
- `docs/maintenance/codex-reference.md` — Keep; ensure consistent with claude-reference consolidation. **Keep**
- `docs/maintenance/file-consolidation-inventory.md` — Keep.
- `docs/maintenance/new-todo.md` — Consolidate with `docs/maintenance/todo.md` to avoid drift. **Deprecate/Consolidate**
- `docs/maintenance/open_processes_index.md` — Keep.
- `docs/maintenance/root-docs-inventory.md` — Update to reflect this audit and current file set. **Update**
- `docs/maintenance/symbol_map.md` — Keep.
- `docs/maintenance/todo.md` — Keep (primary maintenance TODO; align duplicates). **Keep/Consolidate**
- `docs/maintenance/widget-improvements.md` — Keep.

## Docs – Roadmaps, Latest, and UI

- `docs/roadmaps/README.md` — Keep.
- `docs/roadmaps/accounts.md` — Keep.
- `docs/roadmaps/investments.md` — Keep.
- `docs/roadmaps/planning.md` — Keep.
- `docs/roadmaps/product_scoped_accounts.md` — Keep.
- `docs/roadmaps/transactions.md` — Keep.
- `docs/latest/net_changes_feature.md` — Update (see above). **Update**
- `docs/latest/recent_transactions_feature.md` — Update (see above). **Update**
- `docs/ui/planning.md` — Keep.

## Docs – Additional Frontend/Architecture

- `docs/architecture/01_DEV-ArchitectureChecks.md` — Keep.
- `docs/architecture/Plaid_Helpers_Design.md` — Keep.
- `docs/frontend_duplicate_component_review.md` — Move to `docs/frontend/` (duplicate listing above). **Move**

## Docs – Arbitrage/Arbit

- `docs/arbit_dashboard.md` — Move to `docs/frontend/` (see above). **Move/Consolidate**
- `docs/arbitrage_page.md` — Move to `docs/frontend/` (see above). **Move**

## Docs – Miscellaneous

- `docs/maps/link_account_products_map.md` — Keep.
- `docs/maps/repository_map.md` — Update (see above). **Update**
- `docs/migration_plan.md` — Update (see above). **Update**

## Frontend Repo Files

- `frontend/README.md` — Keep.
- `frontend/ANIMATIONS_GUIDE.md` — Keep.
- `frontend/docs/typography-spacing-guide.md` — Keep.
- `frontend/src/api/MIGRATIONS_CHECKLIST.md` — Update; ensure API migration steps are current. **Update**
- `frontend/src/components/forecast/00REF_ForecastDev_Checklist.md` — Update; checklist likely stale. **Update**
- `frontend/src/components/forecast/01REF_Architecture_Design.md` — Update if architecture evolved. **Update**
- `frontend/src/components/forecast/02REF_API_Integration.md` — Update if integration changed. **Update**
- `frontend/src/components/forecast/03REF_Development_Planning.md` — Update for current plan. **Update**
- `frontend/src/components/recurring/00_Recurring_FeatureAudit.md` — Update for latest audit results. **Update**
- `frontend/src/components/recurring/01REF_Specification_Architecture.md` — Update if implementation diverged. **Update**
- `frontend/src/components/recurring/01REF_UserInterface.md` — Update for current UI. **Update**
- `frontend/src/services/MIGRATE_API_SERVICE.md` — Update once migration completed. **Update**
- `frontend/src/views/Mock/DashboardMock.md` — Deprecate or relocate to docs if still needed; mock view notes don't belong in source tree. **Deprecate/Move**
- `frontend/src/views/Mock/DashboardMockLayout.md` — Deprecate or relocate with above. **Deprecate/Move**
- `frontend/src/views/Mock/MockDataCanvas.md` — Deprecate or relocate with above. **Deprecate/Move**

## Scripts

- `scripts/README-CADDY.md` — Keep (script-specific doc is appropriately located). **Keep**

## Cached Artifact

- `.pytest_cache/README.md` — Deprecate/ignore; generated cache, should not require curation. **Deprecate**
