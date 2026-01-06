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
        <ChartDetailsSidebar
          v-model:show7-day="show7DayModel"
          v-model:show30-day="show30DayModel"
          v-model:show-avg-income="showAvgIncomeModel"
          v-model:show-avg-expenses="showAvgExpensesModel"
          v-model:show-comparison-overlay="showComparisonOverlayModel"
          v-model:comparison-mode="comparisonModeModel"
        />
        <div class="flex items-center justify-center mb-4">
          <h2 class="daily-net-chart-title">
            <span class="title-text">Net Income</span>
            <span class="title-subtitle">(Daily)</span>
          </h2>
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
</style>
