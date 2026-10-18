# Dashboard Chart Modal Logic

> **Purpose:** Document the event flow and modal behavior for `Dashboard.vue`. This logic is vital for reviewing transactions directly from charts and must not be removed.

## Charts Emitting Click Events

Both `DailyNetChart.vue` and `CategoryBreakdownChart.vue` emit a `bar-click` event whenever a user clicks on a bar. The event payload represents either the date (daily net chart) or the category label (breakdown chart).

When the breakdown is switched to Merchant mode, merchant bar clicks open the same transaction modal shell used by daily/category drill-downs, but with merchant-specific filtering and non-redundant row fields (description-first details instead of repeating the selected merchant name per row).

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
`useTransactions`, supports keyboard-first shortcuts (← edit, → approve/save, `1-5` focus fields, `Tab` cycles fields, `Enter` saves, `Esc` cancels, `N` starts the next batch, `0` closes the modal), and uses
`updateTransaction` / `createTransactionRule` to persist edits before advancing through each batch.

The dashboard hero exposes the number of transactions in the current review queue. The count uses
the active dashboard date range (and the optional tag filter shown on the review card), and the
indicator opens the same review modal directly. Loading and API failure states are shown in place
of a potentially misleading numeric count.

The review call-to-action card now uses a themed gradient treatment and stronger field/button affordances
to match the dashboard visual language. Inside the modal, editable fields are grouped into bordered
cards and primary/secondary actions are visually separated to make keyboard and pointer workflows
more intuitive without changing existing behavior.

To reinforce keyboard-first affordances, each editable field and primary action now includes a small
themed shortcut chip that mirrors the active key binding.

Review modal action buttons also inherit the shared two-tone button treatment from `main.css`, including
hover highlights and a pressed-state inversion (filled to outlined) so approve/edit/next actions remain
visually distinct while stepping through each batch.

## Daily Net click-through reconciliation (TP-20261017-004)

Clicking a day opens `TransactionModal` with `GET /api/transactions/get_transactions?include_transfers=true` for that day, paged (up to 5 x 1,000 rows) by `utils/dailyModal.js`. Rows carry the backend's `reporting_flow_kind`, `flow_confidence`, `flow_reason_codes`, `signed_account_delta` and `economic_amount`; `utils/flowSummary.js` only adds them up, it never classifies.

- Income / Expense / Net use economic rows only. Transfers in/out, debt payments, investment moves and rows needing classification appear as separate "not in Net" lines; refunds are in Net.
- Pending rows are listed but excluded from totals (the chart uses posted rows) and counted in a notice.
- If the modal's economic totals differ from the clicked chart bucket, or only part of a very large day loaded, a notice says so instead of implying the numbers match.
- `ModalTransactionsDisplay` keeps transfer rows visible but neutral, with a `Transfer` / `Debt payment` / `Investment` / `Review` chip whose tooltip gives the backend reason. A `Review` chip means the backend could not classify the row (for example an unpaired brokerage transfer); it is not a verification. Clicking a row still opens it in Transactions to confirm a transfer pair or edit it.
- Category and merchant modals fed by unclassified endpoints keep the legacy sign-based summary.
- Refresh: the modal closes when a row opens Transactions, and the dashboard (chart and modal) refetch on return; there is no polling.
