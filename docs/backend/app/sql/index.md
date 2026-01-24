# backend/app/sql Documentation

This directory mirrors `backend/app/sql`. Keep documentation filenames aligned with the
code modules and update this index when adding, renaming, or removing SQL helpers.

## Transaction & Account Operations

- [`account_logic.md`](account_logic.md): SQL-level account resolution and user validation.
- [`transactions_logic.md`](transactions_logic.md): Placeholder for transaction SQL helpers (see services/routes docs).
- [`category_logic.md`](category_logic.md): Category inference, overrides, and bulk reclassification.
- [`transaction_rules_logic.md`](transaction_rules_logic.md): Apply user-defined transaction rules during sync.
- [`refresh_metadata.md`](refresh_metadata.md): Upsert Plaid transaction metadata and sanitize payloads.

## Recurring Logic

- [`recurring_logic.md`](recurring_logic.md): Match, link, and schedule recurring transaction sequences.

## Forecasting

- [`forecast_logic.md`](forecast_logic.md): Time-series generation for predictive engines.

## Investment Data

- [`investments_logic.md`](investments_logic.md): Sync Plaid securities, holdings, and investment transactions.

## Import/Export

- [`manual_import_logic.md`](manual_import_logic.md): CSV parsing and ingestion of user-uploaded transaction data.
- [`export_logic.md`](export_logic.md): Structured export of balances and transactions.

## Planning Workflows

- [`planning_logic.md`](planning_logic.md): Manage planning scenarios, bills, and allocation validations.

## SQL Utilities

- [`dialect_utils.md`](dialect_utils.md): Provide dialect-aware INSERT helpers for SQLite and PostgreSQL.
- [`sequence_utils.md`](sequence_utils.md): Keep the `transactions.id` sequence in sync on PostgreSQL.

## Models

- [`models/Account.md`](models/Account.md)
- [`models/AccountHistory.md`](models/AccountHistory.md)
- [`models/Category.md`](models/Category.md)
- [`models/PlaidWebhookLog.md`](models/PlaidWebhookLog.md)
- [`models/RecurringTransaction.md`](models/RecurringTransaction.md)
- [`models/TransactionRule.md`](models/TransactionRule.md)
- [`models/Transactions.md`](models/Transactions.md)
