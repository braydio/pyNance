<!--
  FinancialSummary.vue
  Displays key income, expense, and net metrics derived from DailyNetChart data.
  Users can toggle between basic and extended views with moving averages,
  per-category trends with signed deltas, highest earning/spending days,
  volatility, and basic outlier detection.
-->
<template>
  <div class="statistics-container">
    <!-- Statistics Header with Toggle -->
    <div class="stats-header">
      <h3 class="stats-title">Financial Snapshot</h3>
      <div class="stats-controls">
        <button
          class="stats-toggle-btn"
          :class="{ extended: isExtendedView }"
          @click="toggleExtendedView"
          :title="isExtendedView ? 'Switch to Basic View' : 'Switch to Extended View'"
        >
          {{ isExtendedView ? 'Hide Detail View' : 'Show Detail View' }}
        </button>
      </div>
    </div>

    <!-- Basic Statistics (Always Visible) -->
    <div class="basic-stats">
      <div class="stat-item stat-income">
        <span class="stat-label">Income:</span>
        <span class="stat-value">{{ formatAmount(summary.totalIncome) }}</span>
      </div>
      <div class="stat-item stat-expenses">
        <span class="stat-label">Expenses:</span>
        <span class="stat-value">{{ formatAmount(summary.totalExpenses) }}</span>
      </div>
      <div class="stat-item stat-net" :class="netPolarityClass">
        <span class="stat-label">Net Total:</span>
        <span class="stat-value">{{ formatAmount(summary.totalNet) }}</span>
      </div>
    </div>

    <!-- Extended Statistics (Conditional) -->
    <Transition name="expand">
      <div v-if="isExtendedView" class="extended-stats">
        <div class="stats-grid">
          <!-- Daily Averages -->
          <div class="stat-group">
            <h4 class="group-title">Daily Averages</h4>
            <div class="stat-item">
              <span class="stat-label">Avg Income:</span>
              <span class="stat-value">{{ formatAmount(extendedMetrics.avgDailyIncome) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Avg Expenses:</span>
              <span class="stat-value">{{ formatAmount(extendedMetrics.avgDailyExpenses) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Avg Net:</span>
              <span class="stat-value">{{ formatAmount(extendedMetrics.avgDailyNet) }}</span>
            </div>
          </div>

          <!-- Moving Averages -->
          <div class="stat-group">
            <h4 class="group-title">Moving Averages</h4>
            <div class="stat-item">
              <span class="stat-label">7-Day MA:</span>
              <span class="stat-value">{{ formatAmount(extendedMetrics.netMA7) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">30-Day MA:</span>
              <span class="stat-value">{{ formatAmount(extendedMetrics.netMA30) }}</span>
            </div>
          </div>

          <!-- Trends & Volatility -->
          <div class="stat-group">
            <h4 class="group-title">Trends</h4>
            <div class="stat-item">
              <span class="stat-label">Net Trend:</span>
              <span class="stat-value trend-indicator" :class="netTrendClass">
                {{ netTrendLabel }} {{ formatSignedCurrency(extendedMetrics.netChange) }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Income Trend:</span>
              <span class="stat-value trend-indicator" :class="incomeTrendClass">
                {{ incomeTrendLabel }} {{ formatSignedCurrency(extendedMetrics.incomeChange) }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Expense Trend:</span>
              <span class="stat-value trend-indicator" :class="expenseTrendClass">
                {{ expenseTrendLabel }} {{ formatSignedCurrency(extendedMetrics.expenseChange) }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Volatility:</span>
              <span class="stat-value">{{ volatilityLevel }}</span>
            </div>
          </div>

          <!-- Extremes & Outliers -->
          <div class="stat-group">
            <h4 class="group-title">Outliers</h4>
            <div class="stat-item">
              <span class="stat-label">Top Earning Day:</span>
              <span class="stat-value">{{ topEarningLabel }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Top Spending Day:</span>
              <span class="stat-value">{{ topSpendingLabel }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Outlier Days (>|2σ|):</span>
              <span class="stat-value">{{ extendedMetrics.outlierDays.length }}</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { formatAmount } from '@/utils/format'

/**
 * Format a numeric delta with an explicit sign.
 *
 * @param {number} value - The value to format.
 * @returns {string} Signed currency string.
 */
function formatSignedCurrency(value) {
  const abs = Math.abs(value)
  const formatted = formatAmount(abs)
  return value >= 0 ? `+${formatted}` : `-${formatted}`
}

const props = defineProps({
  summary: {
    type: Object,
    default: () => ({
      totalIncome: 0,
      totalExpenses: 0,
      totalNet: 0,
      highestIncomeDay: null,
      highestExpenseDay: null,
      trend: 0,
      volatility: 0,
      outlierDates: [],
    }),
  },
  chartData: {
    type: Array,
    default: () => [],
  },
  zoomedOut: {
    type: Boolean,
    default: false,
  },
})

// Toggle state for basic/extended view
const isExtendedView = ref(false)

function toggleExtendedView() {
  isExtendedView.value = !isExtendedView.value
}

// Basic computed properties
const netPolarityClass = computed(() => ({
  positive: props.summary.totalNet >= 0,
  negative: props.summary.totalNet < 0,
}))

// Extended statistics calculations
const extendedMetrics = computed(() => {
  const data = props.chartData
  if (!data.length) {
    return {
      avgDailyIncome: 0,
      avgDailyExpenses: 0,
      avgDailyNet: 0,
      netMA7: 0,
      netMA30: 0,
      netTrend: 0,
      incomeTrend: 0,
      expenseTrend: 0,
      netChange: 0,
      incomeChange: 0,
      expenseChange: 0,
      volatility: 0,
      topEarningDay: null,
      topSpendingDay: null,
      outlierDays: [],
    }
  }

  const days = data.length

  // Daily aggregates
  const incomeValues = data.map((d) => d.income?.parsedValue || 0)
  const expenseValues = data.map((d) => Math.abs(d.expenses?.parsedValue || 0))
  const netValues = data.map((d) => d.net?.parsedValue || 0)

  const avgDailyIncome = props.summary.totalIncome / days
  const avgDailyExpenses = props.summary.totalExpenses / days
  const avgDailyNet = props.summary.totalNet / days

  const netMA7 = calculateMovingAverage(netValues, 7)
  const netMA30 = calculateMovingAverage(netValues, 30)

  const netTrend = calculateTrend(netValues)
  const incomeTrend = calculateTrend(incomeValues)
  const expenseTrend = calculateTrend(expenseValues)
  const netChange = netValues[netValues.length - 1] - netValues[0]
  const incomeChange = incomeValues[incomeValues.length - 1] - incomeValues[0]
  const expenseChange = expenseValues[expenseValues.length - 1] - expenseValues[0]
  const volatility = calculateVolatility(netValues)

  // Highest income/expense days
  const maxIncomeIdx = incomeValues.indexOf(Math.max(...incomeValues))
  const maxExpenseIdx = expenseValues.indexOf(Math.max(...expenseValues))
  const topEarningDay = data[maxIncomeIdx]
    ? { date: data[maxIncomeIdx].date, amount: incomeValues[maxIncomeIdx] }
    : null
  const topSpendingDay = data[maxExpenseIdx]
    ? { date: data[maxExpenseIdx].date, amount: expenseValues[maxExpenseIdx] }
    : null

  // Basic outlier detection using 2 standard deviations
  const mean = netValues.reduce((a, b) => a + b, 0) / days
  const threshold = 2 * volatility
  const outlierDays = data
    .filter((d, i) => Math.abs(netValues[i] - mean) > threshold)
    .map((d) => d.date)

  return {
    avgDailyIncome,
    avgDailyExpenses,
    avgDailyNet,
    netMA7,
    netMA30,
    netTrend,
    incomeTrend,
    expenseTrend,
    netChange,
    incomeChange,
    expenseChange,
    volatility,
    topEarningDay,
    topSpendingDay,
    outlierDays,
  }
})

// Trend display helpers
function trendLabel(trend) {
  if (trend > 0.1) return '↗ Increasing'
  if (trend < -0.1) return '↘ Decreasing'
  return '→ Stable'
}

const netTrendClass = computed(() => ({
  'trend-up': extendedMetrics.value.netTrend > 0,
  'trend-down': extendedMetrics.value.netTrend < 0,
  'trend-flat': extendedMetrics.value.netTrend === 0,
}))
const incomeTrendClass = computed(() => ({
  'trend-up': extendedMetrics.value.incomeTrend > 0,
  'trend-down': extendedMetrics.value.incomeTrend < 0,
  'trend-flat': extendedMetrics.value.incomeTrend === 0,
}))
const expenseTrendClass = computed(() => ({
  'trend-up': extendedMetrics.value.expenseTrend > 0,
  'trend-down': extendedMetrics.value.expenseTrend < 0,
  'trend-flat': extendedMetrics.value.expenseTrend === 0,
}))

const netTrendLabel = computed(() => trendLabel(extendedMetrics.value.netTrend))
const incomeTrendLabel = computed(() => trendLabel(extendedMetrics.value.incomeTrend))
const expenseTrendLabel = computed(() => trendLabel(extendedMetrics.value.expenseTrend))

const volatilityLevel = computed(() => {
  const vol = extendedMetrics.value.volatility
  if (vol < 50) return 'Low'
  if (vol < 200) return 'Medium'
  return 'High'
})

const topEarningLabel = computed(() => {
  const hi = extendedMetrics.value.topEarningDay
  if (!hi) return 'N/A'
  const amt = formatAmount(hi.amount)
  // Show explicit plus sign for highest income
  return `${hi.date} (+${amt})`
})

const topSpendingLabel = computed(() => {
  const he = extendedMetrics.value.topSpendingDay
  return he ? `${he.date} (${formatAmount(he.amount)})` : 'N/A'
})

// Statistical calculation functions
function calculateMovingAverage(values, period) {
  if (values.length < period) return values.reduce((a, b) => a + b, 0) / values.length

  const recent = values.slice(-period)
  return recent.reduce((a, b) => a + b, 0) / period
}

function calculateTrend(values) {
  const n = values.length
  if (n < 2) return 0

  const x = Array.from({ length: n }, (_, i) => i)
  const sumX = x.reduce((a, b) => a + b, 0)
  const sumY = values.reduce((a, b) => a + b, 0)
  const sumXY = x.reduce((sum, xi, i) => sum + xi * values[i], 0)
  const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0)

  return (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX)
}

function calculateVolatility(values) {
  const n = values.length
  if (n < 2) return 0

  const mean = values.reduce((a, b) => a + b, 0) / n
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / n
  return Math.sqrt(variance)
}

// Watch for chart data changes to recalculate
watch(
  () => [props.chartData, props.zoomedOut],
  () => {
    // Trigger reactivity by accessing computed
    extendedMetrics.value
  },
  { deep: true },
)
</script>

<style scoped>
.statistics-container {
  background: linear-gradient(135deg, var(--color-bg-dark) 0%, var(--color-bg-sec) 100%);
  border: 1px solid var(--color-accent-cyan);
  border-radius: 12px;
  padding: 1rem;
  margin-top: 1rem;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid var(--divider);
  padding-bottom: 0.5rem;
}

.stats-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-accent-cyan);
  margin: 0;
}

.stats-toggle-btn {
  background: linear-gradient(135deg, var(--color-bg-sec) 0%, var(--color-bg-dark) 100%);
  border: 1px solid var(--color-accent-cyan);
  color: var(--color-accent-cyan);
  padding: 0.25rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.stats-toggle-btn:hover {
  background: linear-gradient(135deg, var(--color-accent-cyan) 0%, var(--color-accent-blue) 100%);
  color: var(--color-bg-dark);
  border-color: var(--color-accent-cyan);
}

.stats-toggle-btn.extended {
  background: linear-gradient(135deg, var(--color-accent-cyan) 0%, var(--color-accent-blue) 100%);
  color: var(--color-bg-dark);
  border-color: var(--color-accent-cyan);
}

.basic-stats {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 120px;
}

.stat-label {
  font-weight: 600;
  font-size: 0.9rem;
}

.stat-value {
  font-weight: 700;
  font-size: 0.95rem;
}

.stat-income .stat-label {
  color: var(--color-accent-cyan);
}

.stat-expenses .stat-label {
  color: var(--color-accent-red);
}

.stat-net.positive .stat-label,
.stat-net.positive .stat-value {
  color: var(--color-accent-cyan);
}

.stat-net.negative .stat-label,
.stat-net.negative .stat-value {
  color: var(--color-accent-red);
}

.extended-stats {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--divider);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.stat-group {
  background: var(--color-bg-dark);
  border: 1px solid var(--divider);
  border-radius: 8px;
  padding: 0.75rem;
}

.group-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-accent-yellow);
  margin: 0 0 0.5rem 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-group .stat-item {
  margin-bottom: 0.25rem;
  font-size: 0.85rem;
  justify-content: space-between;
}

.stat-group .stat-label {
  color: var(--color-text-muted);
}

.stat-group .stat-value {
  color: var(--color-text-light);
}

.trend-indicator {
  font-weight: 700;
}

.trend-up {
  color: var(--color-accent-cyan);
}

.trend-down {
  color: var(--color-accent-red);
}

.trend-flat {
  color: var(--color-accent-yellow);
}

/* Transition animations */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-10px);
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
  transform: translateY(0);
}

/* Responsive design */
@media (max-width: 768px) {
  .basic-stats {
    flex-direction: column;
    gap: 0.75rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stats-header {
    flex-direction: column;
    gap: 0.5rem;
    align-items: stretch;
    text-align: center;
  }
}
</style>
