<!--
  FinancialSummary.vue
  Displays key income, expense, and net metrics derived from DailyNetChart data.
  Users can toggle between basic and extended views with moving averages and trends.
-->
<template>
  <div class="statistics-container">
    <!-- Statistics Header with Toggle -->
    <div class="stats-header">
      <h3 class="stats-title">Financial Summary</h3>
      <div class="stats-controls">
        <button
          class="stats-toggle-btn"
          :class="{ extended: isExtended }"
          @click="toggleView"
          :title="isExtended ? 'Switch to Basic View' : 'Switch to Extended View'"
        >
          {{ isExtended ? 'Basic' : 'Extended' }}
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
      <div class="stat-item stat-net" :class="netClass">
        <span class="stat-label">Net Total:</span>
        <span class="stat-value">{{ formatAmount(summary.totalNet) }}</span>
      </div>
    </div>

    <!-- Extended Statistics (Conditional) -->
    <Transition name="expand">
      <div v-if="isExtended" class="extended-stats">
        <div class="stats-grid">
          <!-- Daily Averages -->
          <div class="stat-group">
            <h4 class="group-title">Daily Averages</h4>
            <div class="stat-item">
              <span class="stat-label">Avg Income:</span>
              <span class="stat-value">{{ formatAmount(extendedStats.avgDailyIncome) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Avg Expenses:</span>
              <span class="stat-value">{{ formatAmount(extendedStats.avgDailyExpenses) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Avg Net:</span>
              <span class="stat-value">{{ formatAmount(extendedStats.avgDailyNet) }}</span>
            </div>
          </div>

          <!-- Moving Averages -->
          <div class="stat-group">
            <h4 class="group-title">Moving Averages</h4>
            <div class="stat-item">
              <span class="stat-label">7-Day MA:</span>
              <span class="stat-value">{{ formatAmount(extendedStats.movingAverage7) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">30-Day MA:</span>
              <span class="stat-value">{{ formatAmount(extendedStats.movingAverage30) }}</span>
            </div>
          </div>

          <!-- Trends & Volatility -->
          <div class="stat-group">
            <h4 class="group-title">Trends</h4>
            <div class="stat-item">
              <span class="stat-label">Trend:</span>
              <span class="stat-value trend-indicator" :class="trendClass">
                {{ trendLabel }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Volatility:</span>
              <span class="stat-value">{{ volatilityLabel }}</span>
            </div>
          </div>

          <!-- Above Average Days -->
          <div class="stat-group">
            <h4 class="group-title">Above Avg Days</h4>
            <div class="stat-item">
              <span class="stat-label">Income:</span>
              <span class="stat-value">{{ summary.aboveAvgIncomeDays }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Expenses:</span>
              <span class="stat-value">{{ summary.aboveAvgExpenseDays }}</span>
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

const props = defineProps({
  summary: {
    type: Object,
    default: () => ({
      totalIncome: 0,
      totalExpenses: 0,
      totalNet: 0,
      aboveAvgIncomeDays: 0,
      aboveAvgExpenseDays: 0,
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
const isExtended = ref(false)

function toggleView() {
  isExtended.value = !isExtended.value
}

// Basic computed properties
const netClass = computed(() => ({
  positive: props.summary.totalNet >= 0,
  negative: props.summary.totalNet < 0,
}))

// Extended statistics calculations
const extendedStats = computed(() => {
  const data = props.chartData
  if (!data.length) {
    return {
      avgDailyIncome: 0,
      avgDailyExpenses: 0,
      avgDailyNet: 0,
      movingAverage7: 0,
      movingAverage30: 0,
      trend: 0,
      volatility: 0,
    }
  }

  const days = data.length

  // Daily averages
  const avgDailyIncome = props.summary.totalIncome / days
  const avgDailyExpenses = props.summary.totalExpenses / days
  const avgDailyNet = props.summary.totalNet / days

  // Moving averages
  const netValues = data.map((d) => d.net?.parsedValue || 0)
  const movingAverage7 = calculateMovingAverage(netValues, 7)
  const movingAverage30 = calculateMovingAverage(netValues, 30)

  // Trend calculation (simple linear regression slope)
  const trend = calculateTrend(netValues)

  // Volatility (standard deviation)
  const volatility = calculateVolatility(netValues)

  return {
    avgDailyIncome,
    avgDailyExpenses,
    avgDailyNet,
    movingAverage7,
    movingAverage30,
    trend,
    volatility,
  }
})

// Trend display
const trendClass = computed(() => ({
  'trend-up': extendedStats.value.trend > 0,
  'trend-down': extendedStats.value.trend < 0,
  'trend-flat': extendedStats.value.trend === 0,
}))

const trendLabel = computed(() => {
  const trend = extendedStats.value.trend
  if (trend > 0.1) return '↗ Improving'
  if (trend < -0.1) return '↘ Declining'
  return '→ Stable'
})

const volatilityLabel = computed(() => {
  const vol = extendedStats.value.volatility
  if (vol < 50) return 'Low'
  if (vol < 200) return 'Medium'
  return 'High'
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
    extendedStats.value
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
