---
Owner: Backend Team
Last Updated: 2025-02-08
Status: Active
---

# Archived Alembic revisions

The `backend/migrations/versions_archived/` directory preserves legacy Alembic
revisions that are no longer part of the active migration chain but remain
useful for historical reference. The archived modules include:

- `backend/migrations/versions_archived/0ac6fddc893b_.py`
- `backend/migrations/versions_archived/3eb1ade5cfec_merge_category_and_metadata_heads.py`
- `backend/migrations/versions_archived/40b08ff58897_b1c2d3e4f5a6_and_9b0c5ac294b7.py`
- `backend/migrations/versions_archived/85a7cc1f25b6_merging_heads_3eb1ade5cfec_and_.py`
- `backend/migrations/versions_archived/f71197d4f032_legacy_models_py_move.py`

These files are retained for auditability and should not be edited except when
performing repository hygiene tasks (formatting, lint updates, or backfills
that keep the archived history readable).
