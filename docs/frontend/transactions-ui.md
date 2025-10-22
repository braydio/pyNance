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
