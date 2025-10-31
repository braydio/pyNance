<template>
  <aside
    class="chart-details-sidebar"
    :class="{ 'chart-details-sidebar--open': isOpen }"
    role="complementary"
    :aria-labelledby="headerId"
    ref="sidebarRef"
  >
    <button
      type="button"
      class="chart-details-sidebar__toggle"
      :aria-expanded="isOpen.toString()"
      :aria-controls="contentId"
      @click="toggleSidebar"
    >
      <span :id="headerId" class="chart-details-sidebar__label">Details</span>
      <span class="chart-details-sidebar__icon" aria-hidden="true">
        <svg viewBox="0 0 20 20" focusable="false" aria-hidden="true">
          <path
            d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 11.1l3.71-3.87a.75.75 0 0 1 1.08 1.04l-4.25 4.43a.75.75 0 0 1-1.08 0L5.21 8.27a.75.75 0 0 1 .02-1.06Z"
            fill="currentColor"
          />
        </svg>
      </span>
      <span class="sr-only">{{ isOpen ? 'Collapse chart details' : 'Expand chart details' }}</span>
    </button>
    <div
      v-show="isOpen"
      :id="contentId"
      class="chart-details-sidebar__content"
      role="region"
      :aria-labelledby="headerId"
    >
      <h3 class="chart-details-sidebar__heading">Details</h3>
      <section class="chart-details-sidebar__section">
        <h4 class="chart-details-sidebar__section-title">Daily Averages</h4>
        <dl class="chart-details-sidebar__metrics">
          <div class="chart-details-sidebar__metric">
            <dt>Income</dt>
            <dd>{{ formatAmount(dailyAverages.income) }}</dd>
          </div>
          <div class="chart-details-sidebar__metric">
            <dt>Expenses</dt>
            <dd>{{ formatAmount(dailyAverages.expenses) }}</dd>
          </div>
          <div class="chart-details-sidebar__metric">
            <dt>Net</dt>
            <dd :class="netClass">{{ formatAmount(dailyAverages.net) }}</dd>
          </div>
        </dl>
      </section>

      <section class="chart-details-sidebar__section">
        <h4 class="chart-details-sidebar__section-title">Trendlines</h4>
        <dl class="chart-details-sidebar__metrics">
          <div class="chart-details-sidebar__metric">
            <dt>7-Day Net</dt>
            <dd>{{ formatAmount(trendlines.net7) }}</dd>
          </div>
          <div class="chart-details-sidebar__metric">
            <dt>30-Day Net</dt>
            <dd>{{ formatAmount(trendlines.net30) }}</dd>
          </div>
          <div class="chart-details-sidebar__metric">
            <dt>30-Day Income</dt>
            <dd>{{ formatAmount(trendlines.income30) }}</dd>
          </div>
          <div class="chart-details-sidebar__metric">
            <dt>30-Day Expenses</dt>
            <dd>{{ formatAmount(trendlines.expenses30) }}</dd>
          </div>
        </dl>
      </section>

      <fieldset class="chart-details-sidebar__fieldset">
        <legend class="sr-only">Chart overlay toggles</legend>
        <label>
          <input
            type="checkbox"
            :checked="show7Day"
            @change="onOptionChange('update:show7Day', $event.target.checked)"
          />
          7 Day Trended
        </label>
        <label>
          <input
            type="checkbox"
            :checked="show30Day"
            @change="onOptionChange('update:show30Day', $event.target.checked)"
          />
          30 Day Trended
        </label>
        <label>
          <input
            type="checkbox"
            :checked="showAvgIncome"
            @change="onOptionChange('update:showAvgIncome', $event.target.checked)"
          />
          Avg Income
        </label>
        <label>
          <input
            type="checkbox"
            :checked="showAvgExpenses"
            @change="onOptionChange('update:showAvgExpenses', $event.target.checked)"
          />
          Avg Expenses
        </label>
      </fieldset>
    </div>
  </aside>
</template>

<script setup>
/**
 * Sidebar displaying chart overlay controls with accessible toggle behavior.
 *
 * Loads in a collapsed state and automatically collapses again whenever the user
 * selects an option or clicks outside the sidebar.
 */
import { ref, toRefs, onMounted, onBeforeUnmount, computed } from 'vue'
import { formatAmount } from '@/utils/format'

const props = defineProps({
  show7Day: { type: Boolean, default: false },
  show30Day: { type: Boolean, default: false },
  showAvgIncome: { type: Boolean, default: false },
  showAvgExpenses: { type: Boolean, default: false },
  summary: {
    type: Object,
    default: () => ({ totalIncome: 0, totalExpenses: 0, totalNet: 0 }),
  },
  chartData: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits([
  'update:show7Day',
  'update:show30Day',
  'update:showAvgIncome',
  'update:showAvgExpenses',
])

const { show7Day, show30Day, showAvgIncome, showAvgExpenses } = toRefs(props)

const isOpen = ref(false)
const sidebarRef = ref(null)
const uniqueId = Math.random().toString(36).slice(2, 9)
const contentId = `chart-details-${uniqueId}`
const headerId = `${contentId}-header`

/**
 * Normalize chart data emitted by DailyNetChart so summary calculations can be
 * reused in the sidebar without duplicating logic in the parent view.
 */
const chartEntries = computed(() =>
  Array.isArray(props.chartData)
    ? props.chartData.filter((item) =>
        item && typeof item === 'object' && 'income' in item && 'expenses' in item && 'net' in item,
      )
    : [],
)

/**
 * Calculate average income, expenses, and net values for the currently visible
 * window of chart data. Falls back to the summary totals when the chart has not
 * yet emitted data.
 */
const dailyAverages = computed(() => {
  if (!chartEntries.value.length) {
    return {
      income: 0,
      expenses: 0,
      net: props.summary?.totalNet || 0,
    }
  }
  const totalDays = chartEntries.value.length
  const sumForKey = (key) =>
    chartEntries.value.reduce((sum, entry) => sum + (entry[key]?.parsedValue ?? 0), 0)
  return {
    income: sumForKey('income') / totalDays,
    expenses: sumForKey('expenses') / totalDays,
    net: sumForKey('net') / totalDays,
  }
})

/**
 * Derive rolling averages for the most recent 7 and 30 day windows. These
 * figures mirror the optional overlays rendered on the main chart so the user
 * can reference the values even when the trendlines are hidden.
 */
const trendlines = computed(() => {
  if (!chartEntries.value.length) {
    return { net7: 0, net30: 0, income30: 0, expenses30: 0 }
  }
  const sorted = [...chartEntries.value].sort((a, b) => (a.date || '').localeCompare(b.date || ''))
  const sliceRange = (days) => {
    const count = Math.max(0, days)
    if (!count) return []
    return sorted.slice(Math.max(0, sorted.length - count))
  }
  const averageForKey = (records, key) => {
    if (!records.length) return 0
    const total = records.reduce((sum, entry) => sum + (entry[key]?.parsedValue ?? 0), 0)
    return total / records.length
  }
  const last7 = sliceRange(7)
  const last30 = sliceRange(30)
  return {
    net7: averageForKey(last7, 'net'),
    net30: averageForKey(last30, 'net'),
    income30: averageForKey(last30, 'income'),
    expenses30: averageForKey(last30, 'expenses'),
  }
})

const netClass = computed(() =>
  dailyAverages.value.net >= 0
    ? 'chart-details-sidebar__positive'
    : 'chart-details-sidebar__negative',
)

const toggleSidebar = () => {
  isOpen.value = !isOpen.value
}

const closeSidebar = () => {
  isOpen.value = false
}

const onOptionChange = (eventName, checked) => {
  emit(eventName, checked)
  closeSidebar()
}

const handleDocumentClick = (event) => {
  if (!isOpen.value) return
  const sidebarEl = sidebarRef.value
  if (!sidebarEl) return
  if (!sidebarEl.contains(event.target)) {
    closeSidebar()
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<style scoped>
.chart-details-sidebar {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.5rem;
  pointer-events: none;
}

.chart-details-sidebar__toggle {
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  border: 1px solid var(--color-accent-cyan);
  background: color-mix(in srgb, var(--color-accent-cyan) 12%, transparent);
  color: var(--color-accent-cyan);
  font-size: 0.85rem;
  font-weight: 600;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease;
}

.chart-details-sidebar__toggle:hover,
.chart-details-sidebar__toggle:focus-visible {
  background: color-mix(in srgb, var(--color-accent-cyan) 22%, transparent);
  color: var(--color-accent-cyan);
  outline: none;
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-accent-cyan) 30%, transparent);
}

.chart-details-sidebar__icon {
  display: inline-flex;
  width: 1rem;
  height: 1rem;
  transition: transform 0.2s ease;
}

.chart-details-sidebar__icon svg {
  width: 100%;
  height: 100%;
}

.chart-details-sidebar--open .chart-details-sidebar__icon {
  transform: rotate(180deg);
}

.chart-details-sidebar__content {
  pointer-events: auto;
  min-width: 14rem;
  max-width: 16rem;
  padding: 0.75rem;
  border-radius: 0.75rem;
  border: 1px solid color-mix(in srgb, var(--color-accent-cyan) 40%, transparent);
  background: color-mix(in srgb, var(--color-bg) 90%, var(--color-accent-cyan) 10%);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  display: grid;
  gap: 0.5rem;
}

.chart-details-sidebar__heading {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--color-accent-cyan);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.chart-details-sidebar__section {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.chart-details-sidebar__section + .chart-details-sidebar__section {
  margin-top: 0.65rem;
}

.chart-details-sidebar__section-title {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: color-mix(in srgb, var(--color-accent-cyan) 70%, var(--color-text-light));
}

.chart-details-sidebar__metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.45rem;
}

.chart-details-sidebar__metric {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0.35rem 0.45rem;
  border-radius: 0.5rem;
  background: color-mix(in srgb, var(--color-bg) 94%, var(--color-accent-cyan) 6%);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--color-accent-cyan) 25%, transparent);
}

.chart-details-sidebar__metric dt {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: color-mix(in srgb, var(--color-text-muted) 80%, var(--color-accent-cyan) 20%);
}

.chart-details-sidebar__metric dd {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  font-family: 'Fira Code', monospace;
  color: var(--color-text-light);
}

.chart-details-sidebar__positive {
  color: var(--color-accent-green);
}

.chart-details-sidebar__negative {
  color: var(--color-accent-red);
}

.chart-details-sidebar__fieldset {
  display: grid;
  gap: 0.4rem;
  margin: 0;
  padding: 0;
  border: 0;
}

.chart-details-sidebar__fieldset label {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.chart-details-sidebar__fieldset input[type='checkbox'] {
  width: 1rem;
  height: 1rem;
  accent-color: var(--color-accent-cyan);
}
</style>
