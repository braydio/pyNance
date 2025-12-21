# Transactions UI Rules

This document standardizes formatting and styling rules for recent transactions displayed under account details in TopAccountSnapshot.

## Date Formatting

- Use short, locale-friendly dates.
- Formatter: `MM/DD/YY` via `Intl.DateTimeFormat('en-US', { month: '2-digit', day: '2-digit', year: '2-digit' })`.
- Fall back to the raw string when parsing fails.

## Amount Formatting

- Use accounting format with 2 decimals and parentheses for negatives.
- Positive amounts tinted with `--color-accent-cyan`; negatives with `--color-accent-red`.
- Zero amounts use default text color.

## Detail Row Styling

- Detail rows use a subtle card-like panel with `border-left` accent and rounded bottom corners.
- Transaction rows show: short date, truncated name, and right-aligned amount.

## Accessibility

- Maintain readable contrast against the panel background.
- Keep interactive focus on the account row that toggled details; details content is read-only.

## Component

- Location: `frontend/src/components/widgets/TopAccountSnapshot.vue`
- Helpers: `formatShortDate`, `format`, `amountClass`.

## Update Transactions Table Virtualization

The editable update transactions table now virtualizes row rendering for large datasets.
Manual test the scroll performance when working with large transaction histories.

Manual test checklist:

1. Navigate to the transactions update screen that renders
   `frontend/src/components/tables/UpdateTransactionsTable.vue`.
2. Load an account or date range with 200+ transactions (seed data or API data).
3. Scroll from top to bottom and confirm row highlights, inline edit actions, and sorting continue to work.
4. Verify the scroll remains smooth and no blank gaps appear as new rows render in.
