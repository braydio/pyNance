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

## Visual Accents

- Active edit rows use a subtle `--color-accent-indigo` edge highlight to differentiate from standard row zebra striping.

## Related Files

- `frontend/src/components/tables/UpdateTransactionsTable.vue`
- `frontend/src/views/Transactions.vue`
