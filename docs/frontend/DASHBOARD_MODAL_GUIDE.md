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
const showModal = ref(false)
const modalTitle = ref('')
const modalTransactions = ref([])

async function openModalByDate(date: string) {
  modalTitle.value = `Transactions for ${date}`
  const res = await fetchTransactions({ date })
  modalTransactions.value = res.data.transactions || []
  showModal.value = true
}

async function openModalByCategory(payload: { label: string; ids: number[] }) {
  modalTitle.value = `Transactions in ${payload.label}`
  const res = await fetchCategoryTransactions({
    category_ids: payload.ids.join(','),
    start_date: catRange.value.start,
    end_date: catRange.value.end,
  })
  modalTransactions.value = res.data.transactions || []
  showModal.value = true
}
```

The modal remains visible until the user triggers the `close` event.

```vue
<TransactionModal
  v-if="showModal"
  :title="modalTitle"
  :transactions="modalTransactions"
  @close="showModal = false" />
```

## Maintenance Notes

- Do **not** strip the `bar-click` listeners or modal helpers when refactoring.
- Keep the fetch helpers in sync with backend API changes.
- Update this guide whenever the modal workflow changes.
