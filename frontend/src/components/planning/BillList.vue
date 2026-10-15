<template>
  <div class="space-y-4">
    <header class="flex flex-wrap items-center justify-between gap-2">
      <div>
        <h3 class="text-lg font-semibold">Upcoming bills</h3>
        <p class="text-sm text-muted">Soonest due first.</p>
      </div>
      <slot name="actions" />
    </header>

    <div
      v-if="sortedBills.length === 0"
      class="rounded border border-dashed border-muted p-6 text-center text-sm text-muted"
    >
      No bills yet. Add one to begin planning this scenario.
    </div>

    <ul v-else class="rounded border border-subtle">
      <li v-for="bill in sortedBills" :key="bill.id" :class="billRowClass(bill)">
        <div class="bill-row__main">
          <button
            class="bill-row__select flex flex-1 flex-col gap-1 text-left"
            type="button"
            :aria-expanded="isExpanded(bill.id) ? 'true' : 'false'"
            :aria-controls="`bill-details-${bill.id}`"
            :data-testid="`bill-toggle-${bill.id}`"
            @click="handleToggle(bill)"
          >
            <span class="text-sm font-semibold text-muted">{{ formatDueDate(bill.dueDate) }}</span>
            <span class="bill-row__name flex flex-wrap items-center gap-2 font-medium">
              {{ bill.name }}
              <span
                v-if="bill.origin === 'predicted'"
                class="predicted-badge"
                title="Predicted from your recurring transaction history, not entered by you"
              >
                Predicted
              </span>
            </span>
            <span class="text-sm text-muted">{{ bill.frequencyLabel }}</span>
          </button>
          <span class="bill-row__amount font-semibold">{{ bill.amountLabel }}</span>
        </div>
        <div
          v-if="isExpanded(bill.id)"
          :id="`bill-details-${bill.id}`"
          class="bill-row__details text-sm"
          :data-testid="`bill-details-${bill.id}`"
        >
          <p v-if="bill.category"><span class="text-muted">Category:</span> {{ bill.category }}</p>
          <p>
            <span class="text-muted">Source:</span>
            {{
              bill.origin === 'predicted'
                ? 'Predicted from recurring transaction history. Edit it to make it yours.'
                : 'Entered by you.'
            }}
          </p>
        </div>
        <div class="bill-row__actions">
          <template v-if="pendingDeleteId === bill.id">
            <span class="text-sm" role="alert">Delete “{{ bill.name }}”?</span>
            <UiButton
              type="button"
              variant="alert"
              :data-testid="`bill-delete-confirm-${bill.id}`"
              @click="confirmDelete(bill.id)"
              >Confirm delete</UiButton
            >
            <UiButton type="button" variant="outline" @click="pendingDeleteId = null"
              >Cancel</UiButton
            >
          </template>
          <template v-else>
            <UiButton
              type="button"
              variant="outline"
              :aria-label="`Edit ${bill.name}`"
              @click.stop="handleEdit(bill)"
              >Edit</UiButton
            >
            <UiButton
              type="button"
              variant="alert"
              :aria-label="`Delete ${bill.name}`"
              :data-testid="`bill-delete-${bill.id}`"
              @click.stop="pendingDeleteId = bill.id"
              >Delete</UiButton
            >
          </template>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import UiButton from '@/components/ui/Button.vue'
import type { Bill, BillFrequency } from '@/types/planning'
import { formatCurrency } from '@/utils/currency'

const props = withDefaults(
  defineProps<{
    bills: Bill[]
    currencyCode?: string
    selectedBillId?: string | null
  }>(),
  {
    bills: () => [],
    currencyCode: 'USD',
    selectedBillId: null,
  },
)

const emit = defineEmits<{
  (_e: 'select', _bill: Bill): void
  (_e: 'edit', _bill: Bill): void
  (_e: 'delete', _id: string): void
}>()

interface DisplayBill extends Bill {
  amountLabel: string
  frequencyLabel: string
}

const sortedBills = computed<DisplayBill[]>(() =>
  [...props.bills]
    .sort((a, b) => a.dueDate.localeCompare(b.dueDate) || a.name.localeCompare(b.name))
    .map((bill) => ({
      ...bill,
      amountLabel: formatCurrency(bill.amountCents / 100, props.currencyCode),
      frequencyLabel: frequencyCopy(bill.frequency),
    })),
)

const expandedIds = ref<Set<string>>(new Set())
const pendingDeleteId = ref<string | null>(null)

function isExpanded(id: string) {
  return expandedIds.value.has(id)
}

/** Select the bill and toggle its details disclosure (keyboard: Enter/Space on the button). */
function handleToggle(bill: Bill) {
  const next = new Set(expandedIds.value)
  if (next.has(bill.id)) next.delete(bill.id)
  else next.add(bill.id)
  expandedIds.value = next
  emit('select', bill)
}

function confirmDelete(id: string) {
  pendingDeleteId.value = null
  handleDelete(id)
}

function handleEdit(bill: Bill) {
  emit('edit', bill)
}

function handleDelete(id: string) {
  emit('delete', id)
}

function formatDueDate(raw: string): string {
  if (!raw) return 'No due date'
  try {
    const date = new Date(raw)
    if (Number.isNaN(date.getTime())) return raw
    return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(date)
  } catch (error) {
    return raw
  }
}

function frequencyCopy(frequency: BillFrequency): string {
  switch (frequency) {
    case 'once':
      return 'One-time'
    case 'weekly':
      return 'Weekly'
    case 'monthly':
      return 'Monthly'
    case 'yearly':
      return 'Annually'
    default:
      return frequency
  }
}

function billRowClass(bill: Bill) {
  return [
    'bill-row flex flex-col flex-wrap gap-3 p-4 sm:flex-row sm:items-center sm:justify-between',
    bill.id === props.selectedBillId ? 'is-selected' : '',
  ]
}
</script>

<style scoped>
.border-subtle {
  border-color: var(--border-subtle);
}

.text-muted {
  color: var(--text-muted);
}

.bill-row {
  background-color: var(--surface-1);
  border-bottom: 1px solid var(--border-subtle);
  min-width: 0;
}

.bill-row__main {
  display: flex;
  flex: 1 1 auto;
  min-width: 0;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.bill-row__select {
  min-width: 0;
  min-height: var(--control-height);
}

.bill-row__select:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}

.bill-row__name {
  overflow-wrap: anywhere;
}

.bill-row__amount {
  flex: none;
  font-variant-numeric: tabular-nums;
}

.bill-row__details {
  flex-basis: 100%;
  display: grid;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  background: var(--surface-2);
}

.bill-row__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.bill-row:last-of-type {
  border-bottom: none;
}

.bill-row.is-selected {
  background-color: var(--accent-surface);
}

.predicted-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background-color: color-mix(in srgb, var(--color-accent-orange) 18%, transparent);
  color: var(--text-warning);
  padding: 0.125rem 0.5rem;
  font-size: 0.8125rem;
  font-weight: 500;
}
</style>
