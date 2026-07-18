---
Owner: Backend Team
Last Updated: 2026-07-16
Status: Active
---

# Transaction Calendar Dates

Revision `7c1e9f4a2b6d` changes `transactions.date` from a timezone-aware timestamp to a SQL `DATE`.

Plaid's core transaction `date` is a calendar date without a time or timezone. Previously, pyNance stored that value as
midnight UTC, which PostgreSQL displayed as the prior evening in timezones west of UTC. The migration converts existing
rows using their UTC calendar value so no transaction changes days.

Exact provider timestamps remain available as timezone-aware values in `plaid_transaction_meta.datetime` and
`plaid_transaction_meta.authorized_datetime` when Plaid supplies them (revision `8d2f0a5b3c7e`).

The downgrade recreates midnight-UTC timestamps from the calendar dates.
