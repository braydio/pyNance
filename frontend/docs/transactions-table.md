# Transactions Table Editing

This guide documents the editable transactions table used on the Transactions view.

## Editable Fields

- Date
- Amount
- Description
- Category
- Merchant

## Editable Field UX

- Each editable field shows the **original value** in a semi-transparent line above the input.
- Inputs include standard UI indicators (icons/prefixes) to clarify what is being edited.

## Amount Styling

- Negative values use `--color-accent-red`.
- Positive values use `--color-accent-green`.
- Zero or empty values fall back to `--color-text-light`.
- The amount input displays a `$` prefix to indicate currency units.

## Filter Summary Overview

When any top-level filter is active on `Transactions.vue` (date range, account, or transaction type), the page renders a summary card above the table with metrics derived from the currently filtered transaction list:

- Total transaction count
- Total summed amount
- Count of unique categories
- Count of unique merchants
- Count of unique accounts
- Count of unique institutions

The summary card is hidden while loading, while showing an error state, or when no top-level filter is selected.

## Visual Accents

- Active edit rows use a subtle `--color-accent-indigo` edge highlight to differentiate from standard row zebra striping.

## Rule Prompt Behavior

- When a user edits `category`, `merchant_name`, or `merchant_type`, the UI opens an explicit confirmation modal asking whether to save a reusable transaction rule.
- The confirmation includes clear **Yes** and **No** actions (`Yes, save rule` / `No, skip rule`) so users can decline rule creation without leaving the flow.
- This behavior is consistent across both the transactions table editor and the step-through transaction review modal.

## Related Files

- `frontend/src/components/tables/UpdateTransactionsTable.vue`
- `frontend/src/views/Transactions.vue`

## Shared Base Primitive Usage

Transactions table control surfaces now rely on base primitives for consistent control geometry and interaction states:

- `BasePanel` wraps the controls surface.
- `BaseSelect` powers account filtering.
- `BaseButton` powers transaction type toggles and pagination actions.
- `BaseChip` renders active filter tags.
- `BaseInput` powers pagination jump-to-page entry.

This keeps border radius, spacing density, border treatment, and focus rings centralized in `frontend/src/components/base/`.
