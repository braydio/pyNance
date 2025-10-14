<template>
  <div class="space-y-4">
    <header class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold">Scheduled bills</h3>
        <p class="text-sm text-muted">Track upcoming expenses for the active scenario.</p>
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
        <button
          class="flex flex-1 flex-col gap-1 text-left"
          type="button"
          @click="handleSelect(bill)"
        >
          <span class="flex items-center gap-2 font-medium">
            {{ bill.name }}
            <span v-if="bill.origin === 'predicted'" class="predicted-badge"> Predicted </span>
          </span>
          <span class="text-sm text-muted">
            {{ formatDueDate(bill.dueDate) }} • {{ bill.frequencyLabel }}
          </span>
        </button>
        <div class="flex flex-col items-end gap-2 sm:flex-row sm:items-center">
          <span class="font-semibold">{{ bill.amountLabel }}</span>
          <UiButton variant="outline" @click.stop="handleEdit(bill)">Edit</UiButton>
          <UiButton variant="alert" @click.stop="handleDelete(bill.id)">Delete</UiButton>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
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
  (e: 'select', bill: Bill): void
  (e: 'edit', bill: Bill): void
  (e: 'delete', id: string): void
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

function handleSelect(bill: Bill) {
  emit('select', bill)
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
    'bill-row flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between',
    bill.id === props.selectedBillId ? 'is-selected' : '',
  ]
}
</script>

<style scoped>
.border-subtle {
  border-color: rgba(148, 163, 184, 0.3);
}

.text-muted {
  color: var(--color-muted, #64748b);
}

.bill-row {
  background-color: var(--color-surface, #fff);
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.bill-row:last-of-type {
  border-bottom: none;
}

.bill-row.is-selected {
  background-color: rgba(59, 130, 246, 0.08);
}

.predicted-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background-color: rgba(234, 179, 8, 0.16);
  color: #92400e;
  padding: 0.125rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
}
</style>
