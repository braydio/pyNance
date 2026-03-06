# Dashboard Chart Modal Logic

> **Purpose:** Document the event flow and modal behavior for `Dashboard.vue`. This logic is vital for reviewing transactions directly from charts and must not be removed.

## Charts Emitting Click Events

Both `DailyNetChart.vue` and `CategoryBreakdownChart.vue` emit a `bar-click` event whenever a user clicks on a bar. The event payload represents either the date (daily net chart) or the category label (breakdown chart).

```vue
<!-- example usage -->
<DailyNetChart @bar-click="openModalByDate" />
<CategoryBreakdownChart @bar-click="openModalByCategory" />
```

## Handling Clicks in `Dashboard.vue`

`Dashboard.vue` listens for these events to fetch the matching transactions and display them in `TransactionModal.vue`:

```ts
const showModal = ref(false);
const modalTitle = ref("");
const modalTransactions = ref([]);

async function openModalByDate(date: string) {
  modalTitle.value = `Transactions for ${date}`;
  const res = await fetchTransactions({ date });
  modalTransactions.value = res.transactions || [];
  showModal.value = true;
}

async function openModalByCategory(payload: { label: string; ids: number[] }) {
  modalTitle.value = `Transactions in ${payload.label}`;
  const res = await fetchTransactions({
    category_ids: payload.ids,
    start_date: catRange.value.start,
    end_date: catRange.value.end,
  });
  modalTransactions.value = res.transactions || [];
  showModal.value = true;
}
```

The modal remains visible until the user triggers the `close` event.

```vue
<TransactionModal
  v-if="showModal"
  :title="modalTitle"
  :transactions="modalTransactions"
  @close="showModal = false"
/>
```

## Maintenance Notes

- Do **not** strip the `bar-click` listeners or modal helpers when refactoring.
- Keep the fetch helpers in sync with backend API changes.
- Category drill-down rows should show each transaction's display category label
  (for example `category_display`) alongside the icon so users can verify the
  exact category assignment from the modal.
- Update this guide whenever the modal workflow changes.

## Review Transactions Overlay

`Dashboard.vue` also exposes a dedicated **Review Transactions** entry point that opens
`TransactionReviewModal.vue`. The modal uses `useDashboardModals` with the `review` key to remain
mutually exclusive with the chart-driven overlays. It fetches transactions in batches of 10 using
`useTransactions`, supports keyboard-first shortcuts (← edit, → approve/save, `1-5` focus fields, `Tab` cycles fields, `Enter` saves, `Esc` cancels), and uses
`updateTransaction` / `createTransactionRule` to persist edits before advancing through each batch.

The review call-to-action card now uses a themed gradient treatment and stronger field/button affordances
to match the dashboard visual language. Inside the modal, editable fields are grouped into bordered
cards and primary/secondary actions are visually separated to make keyboard and pointer workflows
more intuitive without changing existing behavior.
