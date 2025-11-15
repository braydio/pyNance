## 📘 `TransactionsActionsSidebar.vue`

```markdown
# TransactionsActionsSidebar Component

Sidebar component used on the Transactions view to expose file import, search,
and scanner controls.

**Location:** `frontend/src/components/transactions/TransactionsActionsSidebar.vue`

## Responsibilities

- Render the `ImportFileSelector` widget for CSV/OFX import.
- Provide a bound search input for filtering the transactions table.
- Expose a primary button that emits `open-scanner` to toggle the
  Internal Transfer Scanner.

## Props

- `modelValue` (`string`, default `''`): current search query.

## Events

- `update:modelValue` — emitted when the search input changes.
- `open-scanner` — emitted when the "Open Scanner" button is clicked.

## Usage

Used by the `Transactions.vue` view as a sidebar or top control surface for
transaction management. The parent typically binds `v-model` to its own
`searchQuery` ref and listens for `open-scanner` to toggle the scanner panel.
```
