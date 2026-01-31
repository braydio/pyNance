<!--
  NetOverviewSection.vue
  Renders the dashboard hero, date controls, net income chart, and summary widgets.
-->
<template>
  <section class="flex flex-col gap-6">
    <div
      class="h-3 w-full rounded bg-gradient-to-r from-[var(--color-accent-cyan)] via-[var(--color-accent-purple)] to-[var(--color-accent-magenta)] mb-6"
    ></div>
    <div
      class="w-full mb-8 bg-[var(--color-bg-sec)] border-2 border-[var(--color-accent-cyan)] rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-2"
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
    <div
      class="h-3 w-full rounded bg-gradient-to-r from-[var(--color-accent-cyan)] via-[var(--color-accent-purple)] to-[var(--color-accent-magenta)] mb-6"
    ></div>
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
        class="col-span-1 bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-green)] p-4 flex flex-col"
      >
        <TopAccountSnapshot />
      </div>
      <div
        class="md:col-span-2 bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-cyan)] p-6 flex flex-col gap-3 relative"
      >
        <div class="daily-net-chart-header">
          <h2 class="daily-net-chart-title">
            <span class="title-text">Net Income</span>
            <span class="title-subtitle">(Daily)</span>
          </h2>
          <div class="daily-net-chart-separator" aria-hidden="true"></div>
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
                  class="gradient-toggle-btn daily-net-timeframe-btn"
                  :class="{ 'is-active': netTimeframe === 'mtd' }"
                  type="button"
                  :aria-pressed="netTimeframe === 'mtd'"
                  @click="emit('update:net-timeframe', 'mtd')"
                >
                  MTD
                </button>
                <button
                  class="gradient-toggle-btn daily-net-timeframe-btn"
                  :class="{ 'is-active': netTimeframe === 'rolling_30' }"
                  type="button"
                  :aria-pressed="netTimeframe === 'rolling_30'"
                  @click="emit('update:net-timeframe', 'rolling_30')"
                >
                  Rolling 30
                </button>
              </div>
            </div>
          </div>
        </div>

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
        />
      </div>
    </div>

    <div
      class="bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-cyan)] p-6"
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
@import '../../assets/css/main.css';

.username {
  @apply text-[var(--color-accent-cyan)] text-lg;
  text-shadow: 2px 6px 8px var(--bar-gradient-end);
}

.text-muted {
  color: var(--color-text-muted);
}

.daily-net-chart-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-align: center;
}

.daily-net-chart-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.45rem;
  margin-bottom: 0.9rem;
  width: 100%;
}

.daily-net-chart-separator {
  width: 85%;
  height: 1px;
  border-radius: 999px;
  background: var(--divider);
}

.daily-net-chart-controls {
  display: flex;
  justify-content: center;
  width: 100%;
}

.daily-net-chart-toolbar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding: 0.4rem 0.6rem;
  border-radius: 0.35rem;
  border: 1px solid var(--themed-border);
  background: var(--themed-bg);
  backdrop-filter: blur(6px);
}

.title-text {
  background: linear-gradient(135deg, var(--color-accent-cyan) 0%, var(--color-accent-blue) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 20px rgba(113, 156, 214, 0.3);
}

.title-subtitle {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  font-weight: 500;
  opacity: 0.8;
}

.daily-net-timeframe-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.daily-net-timeframe-btn {
  font-size: 0.7rem;
  padding: 0.2rem 0.7rem;
  border-radius: 0.3rem;
  border: 1px solid color-mix(in srgb, var(--color-accent-yellow) 75%, transparent);
  background: color-mix(in srgb, var(--color-bg-dark) 70%, var(--color-accent-yellow) 30%);
  color: var(--color-text-light);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.18);
  line-height: 1;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.daily-net-timeframe-btn:hover,
.daily-net-timeframe-btn:focus-visible {
  background: color-mix(in srgb, var(--color-bg-dark) 45%, var(--color-accent-yellow) 55%);
  color: var(--color-text-light);
  border-color: var(--color-accent-yellow);
  outline: none;
}

.daily-net-timeframe-btn.is-active {
  background: linear-gradient(
    135deg,
    var(--color-accent-yellow) 0%,
    var(--color-accent-green) 100%
  );
  color: var(--color-bg-dark);
  border-color: var(--color-accent-yellow);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.25);
}
</style>
