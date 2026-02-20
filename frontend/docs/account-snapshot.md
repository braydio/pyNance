# Top Account Snapshot Balance Rules

This document defines how `TopAccountSnapshot` resolves and displays balances for accounts and group totals.

## Resolved Balance Field Precedence

`TopAccountSnapshot` resolves each account balance by taking the first finite numeric value in this order:

1. `account.adjusted_balance`
2. `account.balance`
3. `account.balances?.current`
4. fallback to `0` if none of the above are valid numbers

This precedence is implemented in `resolveAccountBalance(account)` and is shared by per-account display and group aggregation logic.

## Negative Presentation

- Currency formatting uses accounting style for negatives: values render as `($123.45)` instead of `-$123.45`.
- Non-credit accounts are styled by sign:
  - positive balances: `bs-balance-pos`
  - negative balances: `bs-balance-neg`
  - zero balances: neutral/no sign class
- Credit accounts are always styled as negative (`bs-balance-neg`) to reflect liability semantics, even when the resolved numeric value is positive.

## Group Total Calculation

The top banner total (`Total Balance`) is the sum of resolved per-account balances for the **currently active group**.

- Per-account values use the same precedence described above.
- The computed total uses `visibleAccounts.reduce((sum, account) => sum + resolveAccountBalance(account), 0)`.
- The total class is then derived from the resulting sign (`bs-total-pos`, `bs-total-neg`, or `bs-total-neutral`).

## Implementation Reference

For exact implementation details, see:

- `frontend/src/components/widgets/TopAccountSnapshot.vue`
