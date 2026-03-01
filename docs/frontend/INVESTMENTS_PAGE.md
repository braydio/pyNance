# Investments Page Overview

Provides a placeholder layout for future investment tracking features.
It includes sections for a portfolio summary, holdings, performance visuals, and transaction review controls.

Route: `/investments`

## Investment transaction filters

The `Recent Investment Transactions` table supports backend-aligned filter query parameters and persists the selected values in local storage.

Available filters:

- `account_id`
- `security_id`
- `type`
- `subtype`
- `start_date`
- `end_date`

Behavior:

- Filter changes immediately refetch transaction data.
- Pagination always resets to page 1 when any transaction filter changes.
- Stored filters are restored when the user revisits or remounts the Investments view.
