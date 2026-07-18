---
Owner: Backend Team
Last Updated: 2026-07-16
Status: Active
---

# Timezone-Aware Plaid Metadata

Revision `8d2f0a5b3c7e` changes `plaid_transaction_meta.datetime` and
`plaid_transaction_meta.authorized_datetime` to timezone-aware timestamps.

Plaid supplies these optional fields as ISO-8601 timestamps with offsets. The migration reconstructs each exact instant
from the original value retained in the raw Plaid payload. Legacy values without a corresponding raw field are
interpreted in `America/New_York`, matching how this deployment previously stored them.

This is separate from `transactions.date`, which remains a timezone-free SQL `DATE` representing the transaction's
calendar posting date.
