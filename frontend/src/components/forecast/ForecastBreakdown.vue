<template>
  <div class="breakdown-panel" data-testid="forecast-breakdown">
    <h3 class="breakdown-header">Forecast Breakdown</h3>

    <template v-if="groups.length">
      <p class="net-line" data-testid="breakdown-net">
        Net change from {{ eventCount }} cash {{ eventCount === 1 ? 'event' : 'events' }}:
        <strong :class="amountPolarityClass(netTotal)">{{ formatSignedCashflow(netTotal) }}</strong>
      </p>
      <ul class="group-list">
        <li v-for="group in groups" :key="group.key">
          <details class="group" :data-testid="`group-${group.key}`">
            <summary class="group-summary">
              <span class="group-label">{{ group.label }}</span>
              <span class="group-count">
                {{ group.rows.length }} {{ group.rows.length === 1 ? 'item' : 'items' }}
              </span>
              <strong class="group-total" :class="amountPolarityClass(group.total)">
                {{ formatSignedCashflow(group.total) }}
              </strong>
            </summary>
            <p v-if="group.hint" class="group-hint">{{ group.hint }}</p>
            <ul class="row-list">
              <li v-for="row in visibleRows(group)" :key="row.key">
                <button
                  type="button"
                  class="line-item-button"
                  :data-testid="`row-${row.key}`"
                  @click="emit('select-item', row.item)"
                >
                  <span class="row-date">{{ row.dateLabel }}</span>
                  <span class="label">{{ row.label }}</span>
                  <span class="amount" :class="amountPolarityClass(row.amount)">
                    {{ formatSignedCashflow(row.amount) }}
                  </span>
                </button>
              </li>
            </ul>
            <button
              v-if="group.rows.length > ROW_LIMIT && !showAll[group.key]"
              type="button"
              class="show-all"
              :data-testid="`show-all-${group.key}`"
              @click="showAll[group.key] = true"
            >
              Show all {{ group.rows.length }}
            </button>
          </details>
        </li>
      </ul>
    </template>
    <p v-else class="breakdown-empty">No forecast cashflows available.</p>

    <details v-if="modelVersion === 'v2'" class="drivers-details" data-testid="forecast-drivers">
      <summary class="drivers-summary">
        What drives this forecast: {{ drivers.length }} scheduled events plus typical spending
      </summary>
      <p class="drivers-note">
        Bills and paychecks below are placed on their expected dates. Everyday spending is estimated
        separately from your recent history, so these events are not counted twice.
      </p>
      <ul v-if="drivers.length" class="drivers-list">
        <li v-for="driver in drivers" :key="driver.event_id" class="driver-row">
          <span class="driver-date">{{ driver.date }}</span>
          <span class="driver-label">{{ driver.label || driver.kind.replace('_', ' ') }}</span>
          <span class="driver-origin" :data-confidence="driver.confidence_label">
            {{ originLabel(driver.origin) }} · {{ driver.confidence_label }} confidence
          </span>
          <strong class="driver-amount">{{ signed(driver.amount) }}</strong>
        </li>
      </ul>
      <p v-else class="breakdown-empty">No scheduled bills or paychecks were detected.</p>

      <div v-if="dataQuality" class="data-quality" data-testid="data-quality">
        <p>
          Based on {{ dataQuality.history_days }} days of history up to {{ dataQuality.as_of_date }}
          <span v-if="dataQuality.confidence"> ({{ dataQuality.confidence }} coverage)</span>.
          <span v-if="dataQuality.proposed_streams">
            {{ dataQuality.proposed_streams }} possible recurring item(s) need more history before
            they are used.
          </span>
        </p>
        <ul v-if="dataQuality.warnings.length" class="data-quality-warnings">
          <li v-for="(warning, index) in dataQuality.warnings" :key="`${warning.code}-${index}`">
            {{ warning.message }}
          </li>
        </ul>
      </div>
    </details>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import type {
  ForecastCashflowItem,
  ForecastDataQuality,
  ForecastDriver,
} from '@/composables/useForecastData'
import { amountPolarityClass, formatSignedCashflow } from '@/utils/format'

const props = withDefaults(
  defineProps<{
    forecastItems: ForecastCashflowItem[]
    viewType: string
    modelVersion?: string
    drivers?: ForecastDriver[]
    dataQuality?: ForecastDataQuality | null
  }>(),
  { modelVersion: 'v1', drivers: () => [], dataQuality: null },
)

const ROW_LIMIT = 15

type GroupKey =
  | 'income'
  | 'bills'
  | 'variable'
  | 'transfers'
  | 'adjustments'
  | 'other_in'
  | 'other_out'

const GROUPS: Array<{ key: GroupKey; label: string; hint?: string }> = [
  { key: 'income', label: 'Expected income' },
  { key: 'bills', label: 'Scheduled bills & payments' },
  {
    key: 'variable',
    label: 'Estimated variable spending',
    hint: 'Typical day-to-day spending estimated from your recent history, shown per day.',
  },
  { key: 'transfers', label: 'Transfers' },
  { key: 'adjustments', label: 'Adjustments' },
  { key: 'other_in', label: 'Other income' },
  { key: 'other_out', label: 'Other spending' },
]

type Row = {
  key: string
  item: ForecastCashflowItem
  amount: number
  cents: number
  label: string
  dateLabel: string
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function groupKeyFor(item: ForecastCashflowItem): GroupKey {
  const category = String(item.category ?? '').toLowerCase()
  if (category === 'scheduled_income') return 'income'
  if (category === 'scheduled_bill' || category === 'liability_payment') return 'bills'
  if (category === 'residual') return 'variable'
  if (category === 'transfer') return 'transfers'
  if (category === 'adjustment' || category.includes('adjust')) return 'adjustments'
  return Number(item.amount) >= 0 ? 'other_in' : 'other_out'
}

function dateLabel(date: string, residual: boolean): string {
  const parsed = new Date(`${date}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return date
  return residual ? `${WEEKDAYS[parsed.getDay()]} ${date}` : date
}

/**
 * Aggregate every cash event once. Events are keyed by `metadata.event_id` when present so the same
 * event can never be counted twice, and totals are summed in whole cents so groups add up exactly.
 */
const groups = computed(() => {
  const seen = new Set<string>()
  const buckets = new Map<GroupKey, Row[]>()
  props.forecastItems.forEach((item, index) => {
    const raw = item.amount as unknown
    if (raw === null || raw === undefined || raw === '') return // never invent zero for missing data
    const amount = Number(raw)
    if (!Number.isFinite(amount)) return
    const eventId = (item.metadata as { event_id?: string } | undefined)?.event_id
    const key = eventId ? `e-${eventId}` : `i-${index}-${item.date}-${item.label}-${amount}`
    if (eventId) {
      if (seen.has(key)) return
      seen.add(key)
    }
    const groupKey = groupKeyFor(item)
    const isResidual = String(item.category ?? '').toLowerCase() === 'residual'
    const row: Row = {
      key,
      item,
      amount,
      cents: Math.round(amount * 100),
      label: isResidual
        ? 'Typical spending'
        : item.label || String(item.category ?? '').replace(/_/g, ' '),
      dateLabel: dateLabel(item.date, isResidual),
    }
    if (!buckets.has(groupKey)) buckets.set(groupKey, [])
    buckets.get(groupKey)!.push(row)
  })
  return GROUPS.filter((group) => buckets.has(group.key)).map((group) => {
    const rows = [...buckets.get(group.key)!].sort((a, b) => a.item.date.localeCompare(b.item.date))
    const totalCents = rows.reduce((sum, row) => sum + row.cents, 0)
    return { ...group, rows, total: totalCents / 100, totalCents }
  })
})

const netTotal = computed(
  () => groups.value.reduce((sum, group) => sum + group.totalCents, 0) / 100,
)
const eventCount = computed(() => groups.value.reduce((sum, group) => sum + group.rows.length, 0))

const showAll = reactive<Record<string, boolean>>({})
const visibleRows = (group: { key: string; rows: Row[] }) =>
  showAll[group.key] ? group.rows : group.rows.slice(0, ROW_LIMIT)

const ORIGIN_LABELS: Record<string, string> = {
  manual_rule: 'Your rule',
  confirmed_recurring: 'Confirmed recurring',
  detected_recurring: 'Detected pattern',
}
const originLabel = (origin: string) => ORIGIN_LABELS[origin] ?? origin
const signed = formatSignedCashflow

const emit = defineEmits<{
  (_event: 'select-item', _item: ForecastCashflowItem): void
}>()
</script>

<style scoped>
@reference "../../assets/css/main.css";
.breakdown-panel {
  background: var(--surface);
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid var(--divider);
}

.breakdown-header {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.drivers-details {
  margin-top: 1rem;
  border-top: 1px solid var(--divider);
  padding-top: 0.75rem;
}

.drivers-summary {
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
}

.drivers-note,
.data-quality {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin: 0.5rem 0;
}

.drivers-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.25rem;
}

.driver-row {
  display: grid;
  grid-template-columns: 6rem 1fr auto;
  gap: 0.5rem;
  align-items: baseline;
  font-size: 0.85rem;
}

.driver-origin {
  grid-column: 2 / 3;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.driver-amount {
  grid-row: 1 / 3;
  grid-column: 3;
}

.net-line {
  margin: 0 0 0.75rem;
  font-size: 0.9375rem;
}

.group-list,
.row-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.5rem;
}

.group {
  border-radius: 0.5rem;
  background: var(--surface-1);
  padding: 0.5rem 0.75rem;
}

.group-summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 0.75rem;
  align-items: baseline;
  cursor: pointer;
}

.group-summary:focus-visible,
.show-all:focus-visible,
.line-item-button:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 2px;
}

.group-label {
  font-weight: 600;
  overflow-wrap: anywhere;
}

.group-count {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.group-total {
  font-variant-numeric: tabular-nums;
}

.group-hint {
  margin: 0.4rem 0 0.25rem;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.row-list {
  margin-top: 0.4rem;
  gap: 0.15rem;
}

.row-date {
  font-size: 0.875rem;
  color: var(--text-muted);
  white-space: nowrap;
}

.show-all {
  margin-top: 0.4rem;
  background: transparent;
  border: none;
  padding: 0.2rem 0;
  color: var(--text-link);
  text-decoration: underline;
  cursor: pointer;
}

.line-item-button {
  width: 100%;
  display: grid;
  grid-template-columns: 8.5rem minmax(0, 1fr) auto;
  gap: 0.75rem;
  align-items: baseline;
  text-align: left;
  padding: 0.4rem 0.5rem;
  border-radius: 0.4rem;
  border: 1px solid transparent;
  background: transparent;
}

.line-item-button:hover {
  border-color: rgba(148, 163, 184, 0.35);
  background: rgba(148, 163, 184, 0.08);
}

.label {
  color: var(--text-muted);
}

.amount {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.label {
  overflow-wrap: anywhere;
}

.breakdown-empty {
  font-size: 0.9rem;
  color: var(--text-muted);
}
</style>
