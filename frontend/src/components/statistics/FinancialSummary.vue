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
          class="gradient-toggle-btn"
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
        <span class="stat-value">{{ formatAmount(detailSummary.totalIncome) }}</span>
      </div>
      <div class="stat-item stat-expenses">
        <span class="stat-label">Expenses:</span>
        <span class="stat-value">{{ formatAmount(detailSummary.totalExpenses) }}</span>
      </div>
      <div class="stat-item stat-net" :class="netPolarityClass">
        <span class="stat-label">Net Total:</span>
        <span class="stat-value">{{ formatAmount(detailSummary.totalNet) }}</span>
      </div>
    </div>

    <!-- Extended Statistics (Conditional) -->
    <Transition name="expand">
      <div v-if="isExtendedView" class="extended-stats">
        <div class="detail-date-controls">
          <label class="detail-date-label" for="financial-snapshot-detail-date"
            >View snapshot as of</label
          >
          <input
            id="financial-snapshot-detail-date"
            v-model="detailDate"
            :max="maxDetailDate"
            :min="minDetailDate"
            type="date"
            class="detail-date-input"
          />
          <button
            v-if="shouldShowResetButton"
            type="button"
            class="detail-date-reset"
            @click="resetDetailDate"
          >
            Reset to today
          </button>
          <p class="detail-date-helper">Showing activity through {{ viewingDateLabel }}</p>
        </div>

        <DailySpendingPanel :detail-date="detailDate" :min-detail-date="minDetailDate" />

        <div class="stats-grid">
          <!-- Averages (Daily + Moving) -->
          <div class="stat-group">
            <h4 class="group-title">Averages</h4>
            <div class="subsection-title">Daily</div>
            <div class="stat-item">
              <span class="stat-label">Income:</span>
              <span class="stat-value">{{ formatAmount(extendedMetrics.avgDailyIncome) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Expenses:</span>
              <span class="stat-value">{{ formatAmount(extendedMetrics.avgDailyExpenses) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Net:</span>
              <span class="stat-value">{{ formatAmount(extendedMetrics.avgDailyNet) }}</span>
            </div>
            <div class="subsection-title">Moving Averages</div>
            <div class="stat-item">
              <span class="stat-label">7-Day:</span>
              <span class="stat-value">{{ formatAmount(extendedMetrics.netMA7) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">30-Day:</span>
              <span class="stat-value">{{ formatAmount(extendedMetrics.netMA30) }}</span>
            </div>
          </div>

          <!-- Trends & Volatility -->
          <div class="stat-group">
            <h4 class="group-title">
              Trends <span class="group-subtitle-inline">{{ trendSummary }}</span>
            </h4>
            <div class="stat-item">
              <span class="stat-label">Net:</span>
              <span class="stat-value trend-indicator" :class="netTrendClass">{{
                formatSignedCurrency(extendedMetrics.netChange)
              }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Income:</span>
              <span class="stat-value trend-indicator" :class="incomeTrendClass">{{
                formatSignedCurrency(extendedMetrics.incomeChange)
              }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Expenses:</span>
              <span class="stat-value trend-indicator" :class="expenseTrendClass">{{
                formatSignedCurrency(extendedMetrics.expenseChange)
              }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Volatility (σ of daily net):</span>
              <span class="stat-value"
                >{{ volatilityLevel }} (σ {{ formatAmount(extendedMetrics.volatility) }})</span
              >
            </div>
          </div>

          <!-- Extremes & Outliers -->
          <div class="stat-group">
            <h4 class="group-title">
              Outliers <span class="group-subtitle-inline">Largest day amounts • 2σ anomalies</span>
            </h4>
            <div class="stat-item">
              <span class="stat-label">Income: <span class="badge-note">largest</span></span>
              <span class="stat-value">{{ topEarningLabel }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Expense: <span class="badge-note">largest</span></span>
              <span class="stat-value">{{ topSpendingLabel }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Anomalies (>|2σ|):</span>
              <span class="stat-value">{{ extendedMetrics.outlierDays.length }}</span>
            </div>
          </div>

          <!-- Savings Metric -->
          <div class="stat-group">
            <h4 class="group-title">Savings</h4>
            <div class="subsection-title">Counts</div>
            <div class="stat-item">
              <span class="stat-label">Positive Days:</span>
              <span class="stat-value">{{ positiveDaysLabel }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Negative Days:</span>
              <span class="stat-value">{{ negativeDaysLabel }}</span>
            </div>
            <div class="subsection-title">Averages</div>
            <div class="stat-item">
              <span class="stat-label">Savings Rate:</span>
              <span class="stat-value">{{ savingsRateLabel }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Savings Amount:</span>
              <span class="stat-value">{{ savingsAmountLabel }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Avg Savings (positive):</span>
              <span class="stat-value">{{ avgPositiveSavingsLabel }}</span>
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
import DailySpendingPanel from './DailySpendingPanel.vue'

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
  startDate: {
    type: String,
    default: '',
  },
  endDate: {
    type: String,
    default: '',
  },
})

// Toggle state for basic/extended view
const isExtendedView = ref(false)

function toggleExtendedView() {
  isExtendedView.value = !isExtendedView.value
}

const TODAY = new Date()
const TODAY_ISO = formatAsISODate(TODAY)

const detailDate = ref(TODAY_ISO)
const userAdjustedDate = ref(false)

const chartDateBounds = computed(() => {
  const data = Array.isArray(props.chartData) ? props.chartData : []
  const sortedDates = data
    .map((entry) => entry?.date)
    .concat([props.startDate, props.endDate])
    .filter((date) => Boolean(parseISODate(date)))
    .sort()

  return {
    min: sortedDates[0] || '',
    max: sortedDates[sortedDates.length - 1] || '',
  }
})

const minDetailDate = computed(() => chartDateBounds.value.min)
const maxDetailDate = computed(() => chartDateBounds.value.max || TODAY_ISO)

/**
 * Compute the default detail date (today clamped within available bounds).
 */
const defaultDetailDate = computed(() =>
  clampDateString(TODAY_ISO, minDetailDate.value, maxDetailDate.value),
)

const shouldShowResetButton = computed(() => detailDate.value !== defaultDetailDate.value)

watch(
  chartDateBounds,
  (bounds) => {
    if (!bounds.max) {
      detailDate.value = TODAY_ISO
      return
    }
    const target = userAdjustedDate.value ? detailDate.value : defaultDetailDate.value
    detailDate.value = clampDateString(target, bounds.min, bounds.max)
  },
  { immediate: true },
)

watch(detailDate, (value, oldValue) => {
  if (value === oldValue) {
    return
  }
  if (!value) {
    detailDate.value = defaultDetailDate.value
    return
  }
  userAdjustedDate.value = value !== defaultDetailDate.value
})

/**
 * Reset the detail snapshot view back to today's date (bounded by data).
 */
function resetDetailDate() {
  userAdjustedDate.value = false
  detailDate.value = defaultDetailDate.value
}

/**
 * Build an inclusive list of date labels between two ISO date strings.
 *
 * @param {string} startISO - Inclusive start date (YYYY-MM-DD).
 * @param {string} endISO - Inclusive end date (YYYY-MM-DD).
 * @returns {string[]} Ordered list of ISO date labels.
 */
function buildDateRangeLabels(startISO, endISO) {
  const start = parseISODate(startISO)
  const end = parseISODate(endISO)
  if (!start || !end) return []

  const labels = []
  const cursor = new Date(Math.min(start, end))
  const last = new Date(Math.max(start, end))
  while (cursor <= last) {
    labels.push(formatAsISODate(cursor))
    cursor.setDate(cursor.getDate() + 1)
  }
  return labels
}

/**
 * Create a zero-filled chart entry for the supplied date label.
 *
 * @param {string} date - ISO date string.
 * @returns {Object} Zero-valued chart entry.
 */
function createZeroFilledEntry(date) {
  return {
    date,
    income: { parsedValue: 0 },
    expenses: { parsedValue: 0 },
    net: { parsedValue: 0 },
    transaction_count: 0,
  }
}

const paddedChartData = computed(() => {
  const data = Array.isArray(props.chartData) ? props.chartData : []
  const parsedStart = parseISODate(props.startDate)
  const parsedDetail = parseISODate(detailDate.value)
  const parsedEnd = parseISODate(props.endDate)

  const sortedDates = data
    .map((d) => parseISODate(d?.date))
    .filter(Boolean)
    .sort((a, b) => a - b)

  const start = parsedStart || sortedDates[0]
  const end = parsedDetail || parsedEnd || sortedDates.at(-1)
  if (!start || !end) {
    return data
  }

  const labels = buildDateRangeLabels(formatAsISODate(start), formatAsISODate(end))
  if (!labels.length) {
    return data
  }

  const byDate = new Map(data.map((entry) => [entry?.date, entry]))
  return labels.map((label) => byDate.get(label) ?? createZeroFilledEntry(label))
})

const filteredChartData = computed(() => {
  const data = paddedChartData.value
  const cutoff = parseISODate(detailDate.value)
  if (!cutoff) {
    return data
  }

  return data.filter((entry) => {
    const entryDate = parseISODate(entry?.date)
    if (!entryDate) {
      return false
    }
    return entryDate <= cutoff
  })
})

const detailSummary = computed(() => {
  const data = filteredChartData.value
  if (!data.length) {
    const hasRawData = Array.isArray(props.chartData) && props.chartData.length > 0
    if (!hasRawData) {
      return {
        totalIncome: props.summary?.totalIncome ?? 0,
        totalExpenses: props.summary?.totalExpenses ?? 0,
        totalNet: props.summary?.totalNet ?? 0,
      }
    }
    return { totalIncome: 0, totalExpenses: 0, totalNet: 0 }
  }

  const totals = data.reduce(
    (acc, entry) => {
      acc.totalIncome += entry?.income?.parsedValue || 0
      acc.totalExpenses += entry?.expenses?.parsedValue || 0
      acc.totalNet += entry?.net?.parsedValue || 0
      return acc
    },
    { totalIncome: 0, totalExpenses: 0, totalNet: 0 },
  )

  return totals
})

const viewingDateLabel = computed(() => {
  const cutoff = parseISODate(detailDate.value)
  if (!cutoff) {
    return 'today'
  }
  return cutoff.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  })
})

// Basic computed properties
const netPolarityClass = computed(() => ({
  positive: detailSummary.value.totalNet >= 0,
  negative: detailSummary.value.totalNet < 0,
}))

// Extended statistics calculations
const extendedMetrics = computed(() => {
  const data = filteredChartData.value
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

  const avgDailyIncome = detailSummary.value.totalIncome / days
  const avgDailyExpenses = detailSummary.value.totalExpenses / days
  const avgDailyNet = detailSummary.value.totalNet / days

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

// Single-line trend summary subtitle
const trendSummary = computed(() => {
  function part(change, label) {
    if (change > 0.01) return `Increasing ${label}`
    if (change < -0.01) return `Decreasing ${label}`
    return `Stable ${label}`
  }
  const income = part(extendedMetrics.value.incomeChange, 'Income')
  const expenses = part(extendedMetrics.value.expenseChange, 'Expenses')
  return `${income} • ${expenses}`
})

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

// Savings metrics
const savingsRateLabel = computed(() => {
  const data = extendedMetrics.value
  // Use sums from arrays to avoid sign confusion
  // incomeValues positive, expenseValues used as abs in extendedMetrics calculations
  // Reconstruct sums from averages where possible
  const days = filteredChartData.value.length
  if (!days) return 'N/A'
  const totalIncome = data.avgDailyIncome * days
  const totalExpensesAbs = Math.abs(data.avgDailyExpenses * days)
  if (totalIncome <= 0) return 'N/A'
  const rate = (totalIncome - totalExpensesAbs) / totalIncome
  const pct = Math.round(rate * 1000) / 10
  return `${pct}%`
})

const savingsAmountLabel = computed(() => {
  if (!filteredChartData.value.length) return 'N/A'
  const totalIncome = detailSummary.value?.totalIncome ?? 0
  const totalExpensesAbs = Math.abs(detailSummary.value?.totalExpenses ?? 0)
  return formatAmount(totalIncome - totalExpensesAbs)
})

const positiveDaysLabel = computed(() => {
  const values = filteredChartData.value.map((d) => d.net?.parsedValue || 0)
  const n = values.length
  if (!n) return 'N/A'
  const pos = values.filter((v) => v > 0).length
  const pct = Math.round((pos / n) * 1000) / 10
  return `${pct}% (${pos}/${n})`
})

const negativeDaysLabel = computed(() => {
  const values = filteredChartData.value.map((d) => d.net?.parsedValue || 0)
  const n = values.length
  if (!n) return 'N/A'
  const neg = values.filter((v) => v < 0).length
  const pct = Math.round((neg / n) * 1000) / 10
  return `${pct}% (${neg}/${n})`
})

const avgPositiveSavingsLabel = computed(() => {
  const values = filteredChartData.value.map((d) => d.net?.parsedValue || 0).filter((v) => v > 0)
  if (!values.length) return 'N/A'
  const avg = values.reduce((a, b) => a + b, 0) / values.length
  return formatAmount(avg)
})

// Watch for chart data changes to recalculate
watch(
  [filteredChartData, () => props.zoomedOut],
  () => {
    extendedMetrics.value
  },
  { deep: true },
)

/**
 * Convert a date string into a Date instance using local timezone.
 *
 * @param {string | Date | undefined | null} input - ISO-like date string or Date.
 * @returns {Date | null} Parsed Date instance, or null if invalid.
 */
function parseISODate(input) {
  if (input instanceof Date) {
    return Number.isNaN(input.getTime()) ? null : input
  }
  if (!input) {
    return null
  }
  const normalized = typeof input === 'string' ? `${input}T00:00:00` : input
  const parsed = new Date(normalized)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

/**
 * Format a Date instance as YYYY-MM-DD.
 *
 * @param {Date} date - Date to format.
 * @returns {string} ISO formatted date string.
 */
function formatAsISODate(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
    return ''
  }
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Clamp a date string so it falls within the specified range.
 *
 * @param {string} value - The target date string.
 * @param {string} min - Lower bound date string.
 * @param {string} max - Upper bound date string.
 * @returns {string} A valid date string within the supplied bounds.
 */
function clampDateString(value, min, max) {
  const parsedValue = parseISODate(value)
  const parsedMin = parseISODate(min)
  const parsedMax = parseISODate(max)

  let result = parsedValue || parsedMax || parseISODate(TODAY_ISO) || new Date()

  if (parsedMin && result < parsedMin) {
    result = parsedMin
  }
  if (parsedMax && result > parsedMax) {
    result = parsedMax
  }

  return formatAsISODate(result)
}
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

.detail-date-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.detail-date-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-muted);
}

.detail-date-input {
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--divider);
  background: var(--color-bg-sec);
  color: var(--color-text-light);
}

.detail-date-input:focus {
  outline: none;
  border-color: var(--color-accent-cyan);
  box-shadow: 0 0 0 2px rgba(0, 217, 255, 0.2);
}

.detail-date-reset {
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  border: 1px solid var(--color-accent-cyan);
  background: transparent;
  color: var(--color-accent-cyan);
  font-size: 0.75rem;
  font-weight: 600;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.detail-date-reset:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(0, 217, 255, 0.25);
}

.detail-date-helper {
  font-size: 0.75rem;
  color: var(--color-text-muted);
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

.group-subtitle-inline {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-muted);
  text-transform: none;
  margin-left: 0.5rem;
}

.stat-group .stat-item {
  margin-bottom: 0.25rem;
  font-size: 0.85rem;
  justify-content: space-between;
}

.subsection-title {
  margin-top: 0.25rem;
  margin-bottom: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-top: 1px dashed var(--divider);
  padding-top: 0.25rem;
}

.stat-group .stat-label {
  color: var(--color-text-muted);
}

.stat-group .stat-value {
  color: var(--color-text-light);
}

.badge-note {
  display: inline-block;
  margin-left: 0.25rem;
  padding: 0 0.35rem;
  font-size: 0.7rem;
  line-height: 1.2;
  color: var(--color-text-muted);
  border: 1px solid var(--divider);
  border-radius: 4px;
  text-transform: lowercase;
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
