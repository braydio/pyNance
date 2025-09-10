Raw Payload Storage Strategy

Overview
- Banking transactions (Plaid Transactions) now persist the full Plaid transaction object into `plaid_transaction_meta.raw`.
- Investments store the full raw objects:
  - `securities.raw` for each security
  - `investment_holdings.raw` for each holding
  - `investment_transactions.raw` for each investment transaction

Rationale
- Auditability and reproducibility of enrichment logic
- Future-proofing for dashboard features without re-calling vendor APIs
- Easier debugging of edge cases and support incidents

Data Volume Notes
- Typical Plaid transaction payloads are small (≈1–2KB). At 50k txns that’s on the order of 50–100MB; acceptable for SQLite/Postgres in most self-hosted scenarios.
- Investment payloads vary by institution but are similar scale. Storing raw alongside denormalized columns provides both query speed and complete detail.

Performance
- Raw JSON columns are not indexed. All existing queries continue to use structured columns.
- Use raw columns for deep inspection, not for hot-path filtering.

Migrations
- New columns added:
  - `plaid_transaction_meta.raw JSON`
  - `securities.raw JSON`
  - `investment_holdings.raw JSON`
  - `investment_transactions.raw JSON`
- Generate and apply Alembic migration before deploying to production.

Security
- Raw payloads may include merchant/counterparty metadata. Ensure database backups are protected. Avoid logging raw JSON to plaintext logs.

Optional File Logging
- File logging for entire API responses remains available via existing helpers to `TEMP_DIR` for ad‑hoc troubleshooting, but database persistence is the source of truth.

