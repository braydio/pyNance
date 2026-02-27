# Documentation Index

All documentation lives in Markdown under `docs/` and mirrors the backend structure for easy lookup.

## Core

- [Backend](../backend/) – server-side code and features
- [Frontend](../frontend/) – client-side components
- [Architecture](../architecture/) – system design overview
- [Process](../process/) – development workflows
- [Maintenance](../maintenance/) – operations and upkeep
- [Maps](../maps/) – diagrams and visual references
- [Roadmaps](../roadmaps/) – active product planning and workstream status

## Additional Resources

- [Dataflow](../dataflow/) – data movement and transformations
- [Forecast](../forecast/) – financial forecasting docs
- [Integrations](../integrations/) – third-party connections
- [Stake Cleanup Audit](../integrations/stake_cleanup.md) – confirmation that the legacy Stake integration has no remaining code paths
- [Devnotes](../devnotes/) – working notes and scratch references
- [Codex](../codex/) – exploratory reports
- [Latest](../latest/) – recent drafts and experiments
- [Financial Summary Detailed](../frontend/FINANCIAL_SUMMARY_DETAILED.md) – DailyNetChart + FinancialSummary wiring details
- [Component Migration Guide](../frontend/component-migration.md) – frontend component organization strategy
- [Tailwind + Vite Style Reference](../frontend/tailwind-vite-style-reference.md) – CSS utilities and build notes
- [Environment Reference](../ENVIRONMENT_REFERENCE.md) – env vars, setup, troubleshooting

## High-Traffic Backend References

- [Transactions API](../backend/app/routes/transactions.md) – primary CRUD surface for accounts and transactions.
- [Investments API](../backend/app/routes/investments.md) – investment accounts, holdings, and transaction query contracts.
- [Transactions Service](../backend/app/services/transactions.md) – ingestion and reconciliation logic powering the Transactions API.
- [Transaction Tags](../backend/features/transaction_tags.md) – tag data model and default serialization behavior.
- [Archived Alembic Revisions](../backend/migrations/versions_archived.md) – historical references for archived migration files.
- [Path Utilities](../backend/app/helpers/path_utils.md) – safe path resolution helpers for backend file access.
- [Forecast Engine Helpers](../backend/forecast/engine.md) – deterministic projection helpers for forecast timelines.
- [Forecast Response Models](../backend/forecast/models.md) – forecast payload structures for timeline, cashflows, and summary data.
- [API Reference](../backend/api-reference.md) – routing conventions and shared API definitions.
- [Transactions Performance Playbook](../backend/performance/transactions.md) – caching, prefetch, and performance notes.
