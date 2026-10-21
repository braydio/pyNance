<!--
  NetOverviewSection.vue
  Renders the dashboard overview, reconnect alert, date controls, net income chart,
  and summary widgets. One selected period (debouncedRange) drives the chart,
  cash direction, financial detail, and transaction count; Safe-to-Spend is an
  independent current-guidance horizon.
-->
<template>
  <section class="flex flex-col gap-6">
    <header class="net-overview-context" data-testid="net-overview-context">
      <h2 class="net-overview-context__title">Overview</h2>
      <p class="net-overview-context__meta">{{ currentDate }}</p>
      <p
        v-if="activityStatusMessage"
        class="net-overview-context__status"
        data-testid="activity-status"
      >
        Activity note: {{ activityStatusMessage }}
      </p>
      <p
        v-if="loadErrorMessage"
        class="net-overview-context__status"
        data-testid="load-error-notice"
        role="status"
      >
        {{ loadErrorMessage }}
      </p>
    </header>

    <div
      v-if="reconnectCount > 0"
      class="surface-attention reconnect-alert p-4 flex flex-wrap items-center justify-between gap-3"
      data-testid="reconnect-alert"
      role="alert"
    >
      <p class="text-sm font-semibold">
        {{ reconnectCount }} {{ reconnectCount === 1 ? 'connection needs' : 'connections need' }}
        reconnection
      </p>
      <router-link to="/accounts" class="btn btn-outline">Reconnect in Accounts</router-link>
    </div>

    <!-- Tier 1: Now -->
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-3 items-stretch" data-testid="now-tier">
      <div class="surface-primary p-4 md:p-6 flex flex-col min-w-0 lg:col-span-2">
        <SafeToSpendCard
          :payload="safeToSpend"
          :loading="safeToSpendLoading"
          :error="safeToSpendError"
          :selected-mode="safeToSpendMode"
          @update:mode="emit('update:safe-to-spend-mode', $event)"
        />
        <p class="text-sm text-muted mt-2" data-testid="safe-to-spend-scope">
          Current guidance (not filtered by chart dates)
        </p>
      </div>
      <div class="now-rail flex flex-col min-w-0" data-testid="now-rail">
        <div class="now-rail__item flex flex-col gap-1" data-testid="cash-out-summary">
          <h3 class="text-sm font-semibold">Money out</h3>
          <p class="text-sm text-muted" data-testid="cash-out-period">{{ periodText }}</p>
          <p v-if="cashOutAvailable" class="net-overview-net" data-testid="cash-out-amount">
            {{ formatAmount(netSummary.totalMoneyOut) }}
          </p>
          <p v-else class="text-sm text-muted" data-testid="cash-out-unavailable">Unavailable</p>
          <p v-if="cashOutAvailable" class="text-sm text-muted" data-testid="cash-out-includes">
            {{ cashOutIncludes }}
          </p>
          <p class="text-sm text-muted">
            Cash paid from your checking and savings accounts. Card purchases count when the card is
            paid, not twice.
          </p>
        </div>
        <div class="now-rail__item flex flex-col gap-1" data-testid="cash-direction">
          <h3 class="text-sm font-semibold">Economic net</h3>
          <p class="text-sm text-muted" data-testid="cash-direction-period">{{ periodText }}</p>
          <p
            class="net-overview-net"
            :class="netSummary.totalNet < 0 ? 'is-negative' : 'is-positive'"
          >
            {{ netSummary.totalNet < 0 ? '▼' : '▲' }} {{ formatAmount(netSummary.totalNet) }}
            <span class="net-overview-net__label">net in selected period</span>
          </p>
          <p class="text-sm text-muted" data-testid="cash-direction-totals">{{ totalsText }}</p>
        </div>
        <div class="now-rail__item flex flex-col gap-2" data-testid="transactions-card">
          <h3 class="text-sm font-semibold">Transactions</h3>
          <p class="net-overview-review-status-text" role="status">{{ transactionCountLabel }}</p>
          <div class="flex flex-wrap items-center gap-2 mt-auto">
            <button
              class="btn btn-outline net-overview-review-status"
              type="button"
              :disabled="periodTransactionCountLoading"
              :aria-label="transactionCountAriaLabel"
              @click="emit('open-review')"
            >
              Review transactions
            </button>
            <button
              class="net-overview-refine-toggle"
              type="button"
              :aria-expanded="showTagFilter"
              @click="showTagFilter = !showTagFilter"
            >
              {{ showTagFilter ? 'Hide filter' : 'Filter by tag' }}
            </button>
          </div>
          <input
            v-if="showTagFilter"
            :value="reviewTagFilter"
            class="input review-filter-input"
            type="text"
            aria-label="Transaction tag filter"
            placeholder="Optional tag (e.g., #groceries)"
            @input="emit('update:review-tag-filter', $event.target.value)"
          />
        </div>
      </div>
    </div>

    <!-- Tier 2: Trend -->
    <div
      class="daily-net-chart-panel net-overview-panel surface-normal p-5 md:p-6 flex flex-col gap-3 relative"
    >
      <div class="flex flex-wrap items-end justify-between gap-2">
        <p class="text-sm text-muted" data-testid="selected-period">{{ periodText }}</p>
        <DateRangeSelector
          :start-date="dateRange.start"
          :end-date="dateRange.end"
          :zoomed-out="zoomedOut"
          @update:start-date="emit('update:start-date', $event)"
          @update:end-date="emit('update:end-date', $event)"
          @update:zoomed-out="emit('update:zoomed-out', $event)"
        />
        <router-link
          class="accent-toggle-btn daily-net-timeframe-btn"
          :to="{
            path: '/charts/cashflow',
            query: { start_date: activeRange.start, end_date: activeRange.end },
          }"
          aria-label="Expand net income chart"
          >Expand chart</router-link
        >
      </div>
      <DailyNetChart
        :basis="netBasis"
        :start-date="activeRange.start"
        :end-date="activeRange.end"
        :zoomed-out="zoomedOut"
        :show7-day="show7Day"
        :show30-day="show30Day"
        :show-avg-income="showAvgIncome"
        :show-avg-expenses="showAvgExpenses"
        :show-comparison-overlay="showComparisonOverlay"
        :timeframe="netTimeframe"
        @summary-change="emit('net-summary-change', $event)"
        @data-change="emit('net-data-change', $event)"
        @bar-click="emit('net-bar-click', $event)"
      >
        <template #title="{ granularityTitle }">
          <div class="daily-net-chart-title-block">
            <div class="net-basis-toggle" role="group" aria-label="Chart measure">
              <button
                v-for="option in NET_BASIS_OPTIONS"
                :key="option.value"
                type="button"
                class="net-basis-btn"
                :class="{ 'is-selected': netBasis === option.value }"
                :aria-pressed="netBasis === option.value"
                :data-testid="`net-basis-${option.value}`"
                @click="netBasis = option.value"
              >
                {{ option.label }}
              </button>
            </div>
            <h2 class="daily-net-chart-title">
              <span class="title-text">{{
                netBasis === 'cash' ? 'Cash Movement' : 'Economic Net'
              }}</span>
              <span class="title-subtitle" data-testid="net-granularity"
                >· {{ granularityTitle }}</span
              >
            </h2>
            <p class="daily-net-chart-totals" data-testid="net-chart-totals">
              {{ netBasis === 'cash' ? cashTotalsText : totalsText }}
            </p>
          </div>
        </template>
        <template #controls="{ granularity }">
          <div class="daily-net-chart-controls">
            <div class="daily-net-chart-toolbar angular-chart-container">
              <ChartDetailsSidebar
                class="chart-details-sidebar--inline"
                :granularity="granularity"
                v-model:show7-day="show7DayModel"
                v-model:show30-day="show30DayModel"
                v-model:show-avg-income="showAvgIncomeModel"
                v-model:show-avg-expenses="showAvgExpensesModel"
                v-model:show-comparison-overlay="showComparisonOverlayModel"
              />
              <div class="daily-net-timeframe-toggle" data-testid="daily-net-timeframe-toggle">
                <button
                  v-for="option in CHART_RANGE_PRESETS"
                  :key="option.value"
                  class="accent-toggle-btn angular-chart-chip daily-net-timeframe-btn"
                  :class="{
                    'accent-toggle-btn--active angular-chart-chip--active':
                      netTimeframe === option.value,
                  }"
                  type="button"
                  :aria-pressed="netTimeframe === option.value"
                  @click="emit('update:net-timeframe', option.value)"
                >
                  {{ option.label }}
                </button>
                <span
                  v-if="netTimeframe === 'custom'"
                  class="daily-net-timeframe-custom"
                  data-testid="daily-net-timeframe-custom"
                >
                  Custom
                </span>
              </div>
            </div>
          </div>
        </template>
      </DailyNetChart>
    </div>

    <div class="net-overview-summary-panel surface-quiet p-4 md:p-5">
      <slot name="summary">
        <FinancialSummary
          :summary="netSummary"
          :chart-data="chartData"
          :zoomed-out="zoomedOut"
          :start-date="activeRange.start"
          :end-date="activeRange.end"
          @select-date="emit('select-date', $event)"
        />
      </slot>
    </div>
  </section>
</template>

<script setup>
/**
 * Net overview section displaying welcome messaging, date controls, and net income charts.
 */
import { computed, ref } from 'vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import ChartDetailsSidebar from '@/components/charts/ChartDetailsSidebar.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'
import { CHART_RANGE_PRESETS } from '@/composables/useDateRange'
import SafeToSpendCard from '@/components/dashboard/SafeToSpendCard.vue'
import FinancialSummary from '@/components/statistics/FinancialSummary.vue'
import { formatAmount } from '@/utils/format'

const props = defineProps({
  currentDate: { type: String, default: '' },
  activityStatusMessage: { type: String, default: '' },
  loadErrorMessage: { type: String, default: '' },
  reconnectCount: { type: Number, default: 0 },
  dateRange: {
    type: Object,
    required: true,
  },
  debouncedRange: {
    type: Object,
    required: true,
  },
  netTimeframe: {
    type: String,
    default: 'mtd',
    validator: (value) =>
      CHART_RANGE_PRESETS.some((option) => option.value === value) || value === 'custom',
  },
  zoomedOut: { type: Boolean, default: false },
  netSummary: { type: Object, required: true },
  chartData: { type: Array, default: () => [] },
  show7Day: { type: Boolean, default: false },
  show30Day: { type: Boolean, default: false },
  showAvgIncome: { type: Boolean, default: false },
  showAvgExpenses: { type: Boolean, default: false },
  showComparisonOverlay: { type: Boolean, default: false },
  safeToSpend: { type: Object, default: null },
  safeToSpendLoading: { type: Boolean, default: false },
  safeToSpendError: { type: String, default: '' },
  safeToSpendMode: { type: String, default: 'today' },
  periodTransactionCount: { type: Number, default: 0 },
  periodTransactionCountLoading: { type: Boolean, default: false },
  periodTransactionCountError: { type: Boolean, default: false },
  reviewTagFilter: { type: String, default: '' },
})

const emit = defineEmits([
  'update:start-date',
  'update:end-date',
  'update:zoomed-out',
  'update:show7-day',
  'update:show30-day',
  'update:show-avg-income',
  'update:show-avg-expenses',
  'update:show-comparison-overlay',
  'update:net-timeframe',
  'update:safe-to-spend-mode',
  'net-summary-change',
  'net-data-change',
  'net-bar-click',
  'select-date',
  'open-review',
  'update:review-tag-filter',
])

const showTagFilter = ref(false)

const NET_BASIS_OPTIONS = [
  { value: 'cash', label: 'Cash Movement' },
  { value: 'economic', label: 'Economic Activity' },
]
/** Cash movement (money through checking and savings) is the default; economic is opt-in. */
const netBasis = ref('cash')

const cashOutAvailable = computed(() => Number.isFinite(props.netSummary?.totalMoneyOut))
const cashOutIncludes = computed(() => {
  const parts = props.netSummary?.cashBreakdown || {}
  const lines = []
  if (parts.debt_payment_out)
    lines.push(`${formatAmount(parts.debt_payment_out)} card and loan payments`)
  if (parts.investment_allocation_out)
    lines.push(`${formatAmount(parts.investment_allocation_out)} allocated to investments`)
  if (parts.external_person_out)
    lines.push(`${formatAmount(parts.external_person_out)} sent to people`)
  if (parts.unclassified_out)
    lines.push(`${formatAmount(parts.unclassified_out)} needs classification`)
  return lines.length
    ? `Includes ${lines.join(' · ')}`
    : 'No card, loan or investment payments in this period'
})
const cashTotalsText = computed(() => {
  const { totalMoneyIn, totalMoneyOut, totalNetCash } = props.netSummary || {}
  if (![totalMoneyIn, totalMoneyOut, totalNetCash].every(Number.isFinite))
    return 'Cash movement unavailable'
  return (
    `Money in ${formatAmount(totalMoneyIn)} · Money out ${formatAmount(totalMoneyOut)} · ` +
    `Net cash ${formatAmount(totalNetCash)}, funding accounts only`
  )
})

/** Refunds are an economic adjustment: disclose them only when the period has any. */
const totalsText = computed(() => {
  const {
    totalIncome = 0,
    totalExpenses = 0,
    totalRefunds = 0,
    totalNet = 0,
  } = props.netSummary || {}
  if (!totalRefunds) {
    return `Income ${formatAmount(totalIncome)} · Expenses ${formatAmount(totalExpenses)}`
  }
  return (
    `Economic income ${formatAmount(totalIncome)} · Expenses ${formatAmount(totalExpenses)} · ` +
    `Refunds ${formatAmount(totalRefunds)} · Net ${formatAmount(totalNet)}, excluding transfers`
  )
})

const transactionCountLabel = computed(() => {
  if (props.periodTransactionCountLoading) return 'Loading transactions…'
  if (props.periodTransactionCountError) return 'Transaction count unavailable'
  if (props.periodTransactionCount === 0) return 'No transactions in this period'
  const noun = props.periodTransactionCount === 1 ? 'transaction' : 'transactions'
  return `${props.periodTransactionCount} ${noun} in selected period`
})

const transactionCountAriaLabel = computed(() => {
  if (props.periodTransactionCountLoading || props.periodTransactionCountError) {
    return transactionCountLabel.value
  }
  return `${transactionCountLabel.value}. Open transaction review.`
})

const show7DayModel = computed({
  get: () => props.show7Day,
  set: (value) => emit('update:show7-day', value),
})
const show30DayModel = computed({
  get: () => props.show30Day,
  set: (value) => emit('update:show30-day', value),
})
const showAvgIncomeModel = computed({
  get: () => props.showAvgIncome,
  set: (value) => emit('update:show-avg-income', value),
})
const showAvgExpensesModel = computed({
  get: () => props.showAvgExpenses,
  set: (value) => emit('update:show-avg-expenses', value),
})
const showComparisonOverlayModel = computed({
  get: () => props.showComparisonOverlay,
  set: (value) => emit('update:show-comparison-overlay', value),
})

/**
 * The single reporting period shown by the chart, cash direction, financial
 * detail, and transaction count.
 */
const activeRange = computed(() => props.debouncedRange)

/**
 * Format an ISO date (YYYY-MM-DD) for the period label without timezone shifts.
 *
 * @param {string} iso - ISO date string.
 * @param {boolean} withYear - Include the year.
 * @returns {string} Display date, or the input when unparseable.
 */
function formatPeriodDate(iso, withYear) {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso || ''))
  if (!match) return String(iso || '')
  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    ...(withYear ? { year: 'numeric' } : {}),
  })
}

const periodText = computed(() => {
  const { start, end } = activeRange.value || {}
  if (!start || !end) return 'Selected period'
  return `Selected period: ${formatPeriodDate(start, false)} – ${formatPeriodDate(end, true)}`
})
</script>

<style scoped>
.net-basis-btn {
  font-size: 0.8125rem;
  padding: 0.2rem 0.6rem;
  line-height: 1;
  border-radius: var(--chart-shell-radius-tight);
  color: var(--color-text-muted);
  border: 1px solid transparent;
}

.net-basis-btn.is-selected {
  color: var(--color-text-light);
  border-color: var(--color-accent-cyan);
}

.net-basis-toggle {
  display: inline-flex;
  gap: 0.25rem;
  margin-bottom: 0.35rem;
}

.net-overview-context__status {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.daily-net-timeframe-custom {
  font-size: 0.8125rem;
  padding: 0.2rem 0.6rem;
  border: 1px dashed var(--divider);
  border-radius: var(--chart-shell-radius-tight);
  color: var(--color-text-muted);
  line-height: 1;
}

.text-muted {
  color: var(--color-text-muted);
}

.daily-net-chart-title {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-align: left;
}

.daily-net-chart-panel {
  position: relative;
  z-index: 8;
  overflow: visible;
  isolation: isolate;
}

.net-overview-context__title {
  font-size: 1.1rem;
  font-weight: 600;
}

.net-overview-context__meta {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.now-rail {
  gap: 1rem;
  padding: 0.25rem 0.25rem 0.25rem 1rem;
}

.now-rail__item + .now-rail__item {
  padding-top: 1rem;
  border-top: 1px solid var(--divider);
}

@media (max-width: 1023px) {
  .now-rail {
    padding-left: 0.25rem;
  }
}

.net-overview-review-status-text {
  font-size: 0.9375rem;
  font-weight: 600;
}

.net-overview-refine-toggle {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  text-decoration: underline;
}

.net-overview-net {
  font-size: 1.5rem;
  font-weight: 700;
}

.net-overview-net.is-negative {
  color: var(--color-danger, #dc2626);
}

.net-overview-net__label {
  font-size: 0.8125rem;
  font-weight: 400;
  color: var(--color-text-muted);
}

.net-overview-review-status {
  cursor: pointer;
}

.net-overview-review-status:hover:not(:disabled),
.net-overview-review-status:focus-visible {
  border-color: var(--color-accent-cyan);
  box-shadow: 0 0 16px color-mix(in srgb, var(--color-accent-cyan) 28%, transparent);
  transform: translateY(-1px);
}

.net-overview-review-status:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 3px;
}

.net-overview-review-status:disabled {
  cursor: wait;
  opacity: 0.75;
}

.net-overview-panel {
  border: 0;
  box-shadow: var(--depth-shadow-resting);
}

.net-overview-panel--accent-cyan {
  border-width: 2px;
  border-color: var(--edge-contrast-accent-cyan);
}

.net-overview-panel--accent-green {
  border-width: 2px;
  border-color: var(--edge-contrast-accent-green);
}

.net-overview-summary-panel {
  position: relative;
  z-index: 1;
}

.daily-net-chart-controls {
  display: flex;
  justify-content: flex-start;
  flex: 0 0 auto;
  position: relative;
  z-index: 12;
}

.daily-net-chart-title-block {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.daily-net-chart-totals {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.daily-net-chart-toolbar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  flex-wrap: wrap;
  padding: 0.35rem 0.45rem;
  border-radius: var(--chart-shell-radius);
  border-color: var(--chart-shell-border);
  background: var(--chart-shell-bg);
  backdrop-filter: blur(6px);
  position: relative;
  z-index: 12;
  box-shadow: var(--chart-shell-shadow);
}

.title-text {
  background: linear-gradient(135deg, var(--color-accent-cyan) 0%, var(--color-accent-blue) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 20px rgba(113, 156, 214, 0.3);
}

.title-subtitle {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  font-weight: 500;
  opacity: 0.8;
}

.daily-net-timeframe-toggle {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.daily-net-timeframe-btn {
  font-size: 0.8125rem;
  padding: 0.2rem 0.6rem;
  border-radius: var(--chart-shell-radius-tight);
  line-height: 1;
}

@media (max-width: 900px) {
  .daily-net-chart-controls {
    width: 100%;
    justify-content: flex-start;
  }

  .daily-net-chart-toolbar {
    justify-content: flex-start;
    border-radius: 16px;
  }
}
</style>
