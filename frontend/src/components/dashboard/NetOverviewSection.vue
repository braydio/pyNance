<!--
  NetOverviewSection.vue
  Renders the dashboard hero, date controls, net income chart, and summary widgets.
-->
<template>
  <section class="flex flex-col gap-6">
    <div class="angular-divider mb-2" aria-hidden="true">
      <span class="angular-divider__rule"></span>
      <span class="angular-divider__step"></span>
    </div>
    <div
      class="net-overview-hero w-full mb-8 bg-[var(--color-bg-sec)] ui-radius-2 p-6 md:p-7 flex flex-col items-center gap-2"
    >
      <h1
        class="text-4xl md:text-5xl font-extrabold tracking-wide text-[var(--color-accent-cyan)] mb-2 drop-shadow"
      >
        Welcome, <span class="username">{{ userName }}</span
        >!
      </h1>
      <p class="text-lg text-muted">Today is {{ currentDate }}</p>
      <p class="italic text-muted">{{ netWorthMessage }}</p>
    </div>
    <div class="angular-divider mb-2" aria-hidden="true">
      <span class="angular-divider__rule"></span>
      <span class="angular-divider__step"></span>
    </div>
    <div class="flex justify-end mb-4">
      <DateRangeSelector
        :start-date="dateRange.start"
        :end-date="dateRange.end"
        :zoomed-out="zoomedOut"
        @update:start-date="emit('update:start-date', $event)"
        @update:end-date="emit('update:end-date', $event)"
        @update:zoomed-out="emit('update:zoomed-out', $event)"
      />
    </div>
    <div class="grid grid-cols-1 gap-6 md:grid-cols-3 items-stretch">
      <div
        class="net-overview-panel net-overview-panel--accent-green col-span-1 bg-[var(--color-bg-sec)] ui-radius-2 p-4 flex flex-col"
      >
        <TopAccountSnapshot />
      </div>
      <div
        class="daily-net-chart-panel net-overview-panel net-overview-panel--accent-cyan md:col-span-2 bg-[var(--color-bg-sec)] ui-radius-2 p-5 md:p-6 flex flex-col gap-3 relative"
      >
        <DailyNetChart
          :start-date="activeRange.start"
          :end-date="activeRange.end"
          :zoomed-out="zoomedOut"
          :show7-day="show7Day"
          :show30-day="show30Day"
          :show-avg-income="showAvgIncome"
          :show-avg-expenses="showAvgExpenses"
          :show-comparison-overlay="showComparisonOverlay"
          :comparison-mode="comparisonMode"
          :timeframe="netTimeframe"
          @summary-change="emit('net-summary-change', $event)"
          @data-change="emit('net-data-change', $event)"
          @bar-click="emit('net-bar-click', $event)"
        >
          <template #title>
            <div class="daily-net-chart-title-block">
              <h2 class="daily-net-chart-title">
                <span class="title-text">Net Income</span>
                <span class="title-subtitle">(Daily)</span>
              </h2>
              <p class="daily-net-chart-totals">
                Income {{ formatAmount(netSummary.totalIncome) }} · Expenses
                {{ formatAmount(netSummary.totalExpenses) }}
              </p>
            </div>
          </template>
          <template #controls>
            <div class="daily-net-chart-controls">
              <div class="daily-net-chart-toolbar">
                <ChartDetailsSidebar
                  class="chart-details-sidebar--inline"
                  v-model:show7-day="show7DayModel"
                  v-model:show30-day="show30DayModel"
                  v-model:show-avg-income="showAvgIncomeModel"
                  v-model:show-avg-expenses="showAvgExpensesModel"
                  v-model:show-comparison-overlay="showComparisonOverlayModel"
                  v-model:comparison-mode="comparisonModeModel"
                />
                <div class="daily-net-timeframe-toggle" data-testid="daily-net-timeframe-toggle">
                  <button
                    class="accent-toggle-btn daily-net-timeframe-btn"
                    :class="{ 'accent-toggle-btn--active': netTimeframe === 'mtd' }"
                    type="button"
                    :aria-pressed="netTimeframe === 'mtd'"
                    @click="emit('update:net-timeframe', 'mtd')"
                  >
                    MTD
                  </button>
                  <button
                    class="accent-toggle-btn daily-net-timeframe-btn"
                    :class="{ 'accent-toggle-btn--active': netTimeframe === 'rolling_30' }"
                    type="button"
                    :aria-pressed="netTimeframe === 'rolling_30'"
                    @click="emit('update:net-timeframe', 'rolling_30')"
                  >
                    Rolling 30
                  </button>
                </div>
              </div>
            </div>
          </template>
        </DailyNetChart>
      </div>
    </div>

    <div
      class="net-overview-summary-panel net-overview-panel net-overview-panel--accent-cyan bg-[var(--color-bg-sec)] ui-radius-2 p-5 md:p-6"
    >
      <slot name="summary">
        <FinancialSummary
          :summary="netSummary"
          :chart-data="chartData"
          :zoomed-out="zoomedOut"
          :start-date="activeRange.start"
          :end-date="activeRange.end"
        />
      </slot>
    </div>
  </section>
</template>

<script setup>
/**
 * Net overview section displaying welcome messaging, date controls, and net income charts.
 */
import { computed } from 'vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import ChartDetailsSidebar from '@/components/charts/ChartDetailsSidebar.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'
import TopAccountSnapshot from '@/components/widgets/TopAccountSnapshot.vue'
import FinancialSummary from '@/components/statistics/FinancialSummary.vue'
import { formatAmount } from '@/utils/format'

const props = defineProps({
  userName: { type: String, default: 'Guest' },
  currentDate: { type: String, default: '' },
  netWorthMessage: { type: String, default: '' },
  dateRange: {
    type: Object,
    required: true,
  },
  debouncedRange: {
    type: Object,
    required: true,
  },
  netRange: {
    type: Object,
    default: null,
  },
  netTimeframe: {
    type: String,
    default: 'mtd',
    validator: (value) => ['mtd', 'rolling_30'].includes(value),
  },
  zoomedOut: { type: Boolean, default: false },
  netSummary: { type: Object, required: true },
  chartData: { type: Array, default: () => [] },
  show7Day: { type: Boolean, default: false },
  show30Day: { type: Boolean, default: false },
  showAvgIncome: { type: Boolean, default: false },
  showAvgExpenses: { type: Boolean, default: false },
  showComparisonOverlay: { type: Boolean, default: false },
  comparisonMode: { type: String, default: 'prior_month_to_date' },
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
  'update:comparison-mode',
  'update:net-timeframe',
  'net-summary-change',
  'net-data-change',
  'net-bar-click',
])

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
const comparisonModeModel = computed({
  get: () => props.comparisonMode,
  set: (value) => emit('update:comparison-mode', value),
})

/**
 * Net visualization date boundaries, preferring the provided net range while
 * falling back to the shared debounced range when no override is supplied.
 */
const activeRange = computed(() => props.netRange || props.debouncedRange)
</script>

<style scoped>
.username {
  color: var(--color-accent-cyan);
  font-size: 1.125rem;
  font-weight: 600;
  text-shadow: 2px 6px 8px var(--bar-gradient-end);
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

.net-overview-hero {
  border: 2px solid var(--edge-contrast-accent-cyan);
  box-shadow: var(--depth-inner-glow), var(--depth-shadow-raised);
}

.net-overview-panel {
  border: 1px solid var(--edge-contrast-1);
  box-shadow: var(--depth-inner-glow), var(--depth-shadow-resting);
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

.angular-divider {
  position: relative;
  height: 0.65rem;
}

.angular-divider__rule {
  position: absolute;
  inset: auto 0 0 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    color-mix(in srgb, var(--color-accent-cyan) 75%, transparent) 0%,
    color-mix(in srgb, var(--color-accent-purple) 80%, transparent) 45%,
    color-mix(in srgb, var(--color-accent-magenta) 74%, transparent) 100%
  );
}

.angular-divider__step {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 5.5rem;
  height: 0.45rem;
  clip-path: polygon(0 100%, 18% 0, 100% 0, 82% 100%);
  background: color-mix(in srgb, var(--color-accent-cyan) 38%, transparent);
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
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.daily-net-chart-toolbar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  flex-wrap: wrap;
  padding: 0.35rem 0.45rem;
  border-radius: 999px;
  border: 1px solid var(--themed-border);
  background: color-mix(in srgb, var(--themed-bg) 88%, transparent);
  backdrop-filter: blur(6px);
  position: relative;
  z-index: 12;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.14);
}

.title-text {
  background: linear-gradient(135deg, var(--color-accent-cyan) 0%, var(--color-accent-blue) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 20px rgba(113, 156, 214, 0.3);
}

.title-subtitle {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-weight: 500;
  opacity: 0.8;
}

.daily-net-timeframe-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.daily-net-timeframe-btn {
  font-size: 0.65rem;
  padding: 0.15rem 0.55rem;
  border-radius: 0.3rem;
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
