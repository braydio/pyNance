<!--
  DailySpendingPanel.vue
  Displays a single-day stacked spending chart with a latest transactions list.
-->
<template>
  <section class="daily-spending-panel">
    <header class="panel-header">
      <div>
        <h4 class="panel-title">Today's Spending</h4>
        <p class="panel-subtitle">Snapshot for {{ formattedDetailDate }}</p>
      </div>
      <div class="panel-controls">
        <label class="average-toggle">
          <input v-model="compareToAverage" type="checkbox" />
          <span>Compare to average profile</span>
        </label>
      </div>
    </header>

    <div class="panel-content">
      <div class="chart-card">
        <canvas ref="chartCanvas" class="chart-canvas"></canvas>
        <div v-if="categoryLoading" class="panel-state">Loading today's spending...</div>
        <div v-else-if="categoryError" class="panel-state panel-state-error">
          Unable to load spending breakdown.
        </div>
        <div v-else-if="isCategoryEmpty" class="panel-state">No spending yet today.</div>
      </div>

      <div class="transactions-card">
        <h5 class="transactions-title">Latest Transactions</h5>
        <div v-if="transactionsLoading" class="panel-state">Loading transactions...</div>
        <div v-else-if="transactionsError" class="panel-state panel-state-error">
          Unable to load transactions.
        </div>
        <div v-else-if="!transactions.length" class="panel-state">No transactions found.</div>
        <ul v-else class="transactions-list">
          <li
            v-for="transaction in transactions"
            :key="transaction.transaction_id || transaction.id || transaction.name"
            class="transaction-row"
          >
            <div class="transaction-meta">
              <span class="transaction-name">{{ transactionLabel(transaction) }}</span>
              <span class="transaction-date">{{ formatTransactionDate(transaction.date) }}</span>
            </div>
            <span class="transaction-amount">{{ formatAmount(transaction.amount) }}</span>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onUnmounted, nextTick } from 'vue'
import { Chart } from 'chart.js/auto'
import { fetchCategoryBreakdownTree } from '@/api/charts'
import { fetchTransactions } from '@/api/transactions'
import { formatAmount } from '@/utils/format'
import { getAccentColor } from '@/utils/colors'

/**
 * Daily spending panel props.
 */
const props = defineProps({
  detailDate: {
    type: String,
    required: true,
  },
  minDetailDate: {
    type: String,
    required: true,
  },
})

const chartCanvas = ref(null)
const chartInstance = ref(null)
const categoryRows = ref([])
const categoryLoading = ref(false)
const categoryError = ref('')
const transactions = ref([])
const transactionsLoading = ref(false)
const transactionsError = ref('')
const compareToAverage = ref(false)
const averageRows = ref([])

const formattedDetailDate = computed(() => {
  const parsed = parseISODate(props.detailDate)
  if (!parsed) {
    return 'today'
  }
  return parsed.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  })
})

const isCategoryEmpty = computed(() => !categoryRows.value.length && !categoryLoading.value && !categoryError.value)

/**
 * Retrieve a CSS variable value from the document root.
 *
 * @param {string} name - CSS custom property name.
 * @returns {string} Resolved CSS value.
 */
function getStyleValue(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

/**
 * Parse an ISO date string into a Date instance.
 *
 * @param {string} value - ISO date string.
 * @returns {Date|null} Parsed date, if valid.
 */
function parseISODate(value) {
  if (!value) {
    return null
  }
  const parsed = new Date(`${value}T00:00:00`)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

/**
 * Normalize a category tree into top-level totals.
 *
 * @param {Array} nodes - Category tree nodes.
 * @returns {Array<{ label: string, amount: number }>} Totals for each category.
 */
function normalizeCategoryTotals(nodes = []) {
  return (nodes || [])
    .map((node) => {
      const childTotal = (node.children || []).reduce((sum, child) => sum + Number(child.amount || 0), 0)
      const amount = Number.isFinite(Number(node.amount)) ? Number(node.amount) : childTotal
      return {
        label: node.label || 'Category',
        amount,
      }
    })
    .filter((row) => row.amount > 0)
    .sort((a, b) => b.amount - a.amount)
}

/**
 * Apply an alpha value to a CSS color string.
 *
 * @param {string} color - CSS color value (hex or rgb).
 * @param {number} alpha - Opacity from 0 to 1.
 * @returns {string} RGBA color string with the requested alpha.
 */
function applyAlphaToColor(color, alpha) {
  if (!color) {
    return color
  }
  if (color.startsWith('rgb(')) {
    return color.replace('rgb(', 'rgba(').replace(')', `, ${alpha})`)
  }
  if (color.startsWith('#')) {
    const raw = color.replace('#', '')
    const hex = raw.length === 3 ? raw.split('').map((ch) => `${ch}${ch}`).join('') : raw
    const parsed = Number.parseInt(hex, 16)
    if (!Number.isNaN(parsed) && hex.length === 6) {
      const r = (parsed >> 16) & 255
      const g = (parsed >> 8) & 255
      const b = parsed & 255
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }
  }
  return color
}

/**
 * Calculate the number of days in an inclusive date range.
 *
 * @param {string} startDate - ISO start date.
 * @param {string} endDate - ISO end date.
 * @returns {number} Number of days, or 0 for invalid ranges.
 */
function getInclusiveDayCount(startDate, endDate) {
  const start = parseISODate(startDate)
  const end = parseISODate(endDate)
  if (!start || !end) {
    return 0
  }
  const msInDay = 24 * 60 * 60 * 1000
  const dayDiff = Math.floor((end.getTime() - start.getTime()) / msInDay)
  return dayDiff >= 0 ? dayDiff + 1 : 0
}

/**
 * Align average rows to the ordering of the base rows.
 *
 * @param {Array<{ label: string, amount: number }>} baseRows - Today's category totals.
 * @param {Array<{ label: string, amount: number }>} avgRows - Average category totals.
 * @returns {Array<{ label: string, amount: number }>} Ordered averages.
 */
function alignAverageRows(baseRows, avgRows) {
  if (!baseRows.length) {
    return avgRows
  }
  const avgMap = new Map(avgRows.map((row) => [row.label, row]))
  const baseLabels = new Set(baseRows.map((row) => row.label))
  const ordered = baseRows.map((row) => avgMap.get(row.label)).filter(Boolean)
  const remaining = avgRows.filter((row) => !baseLabels.has(row.label))
  return [...ordered, ...remaining]
}

/**
 * Destroy any existing Chart.js instance before rendering a new one.
 */
function destroyChart() {
  const canvasEl = chartCanvas.value
  if (chartInstance.value) {
    chartInstance.value.destroy()
    chartInstance.value = null
  }
  if (canvasEl && Chart.getChart) {
    const existing = Chart.getChart(canvasEl)
    if (existing) {
      existing.destroy()
    }
 }
}

/**
 * Render the stacked bar chart for today's category totals and optional averages.
 *
 * @param {Array<{ label: string, amount: number }>} rows - Category totals.
 * @param {Array<{ label: string, amount: number }>} avgRows - Average category totals.
 * @returns {Promise<void>} Resolves after chart rendering completes.
 */
async function renderChart(rows, avgRows) {
  await nextTick()
  const canvasEl = chartCanvas.value
  if (!canvasEl) {
    return
  }
  destroyChart()
  if (!rows.length && !avgRows.length) {
    return
  }
  const ctx = canvasEl.getContext('2d')
  if (!ctx) {
    return
  }
  const showAverage = compareToAverage.value && avgRows.length
  const orderedAverageRows = showAverage ? alignAverageRows(rows, avgRows) : []
  const baseDatasets = rows.map((row, idx) => ({
    label: row.label,
    data: [row.amount],
    backgroundColor: getAccentColor(idx),
    borderRadius: 8,
    borderSkipped: false,
    stack: 'today-stack',
    order: 1,
  }))
  const averageDatasets = orderedAverageRows.map((row, idx) => {
    const accentColor = getAccentColor(idx)
    return {
      label: `${row.label} (Avg)`,
      data: [row.amount],
      backgroundColor: applyAlphaToColor(accentColor, 0.35),
      borderColor: accentColor,
      borderRadius: 8,
      borderSkipped: false,
      borderWidth: 2,
      stack: 'average-stack',
      barPercentage: 0.6,
      categoryPercentage: 0.6,
      order: 2,
    }
  })
  const datasets = [...baseDatasets, ...averageDatasets]
  if (!datasets.length) {
    return
  }

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Today'],
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 16, bottom: 8, left: 12, right: 12 } },
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            color: getStyleValue('--color-text-light'),
            boxWidth: 12,
            boxHeight: 12,
            padding: 12,
          },
        },
        tooltip: {
          callbacks: {
            label: (context) => `${context.dataset.label}: ${formatAmount(context.parsed.y || 0)}`,
          },
          backgroundColor: getStyleValue('--theme-bg'),
          titleColor: getStyleValue('--color-accent-yellow'),
          bodyColor: getStyleValue('--color-text-light'),
          borderColor: getStyleValue('--color-accent-yellow'),
          borderWidth: 1,
        },
      },
      scales: {
        x: {
          stacked: true,
          grid: { color: getStyleValue('--divider') },
          ticks: {
            color: getStyleValue('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 12 },
          },
        },
        y: {
          stacked: true,
          beginAtZero: true,
          grid: { color: getStyleValue('--divider') },
          ticks: {
            color: getStyleValue('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 12 },
            callback: (value) => formatAmount(value),
          },
        },
      },
    },
  })
}

/**
 * Load category breakdown data for the selected detail date.
 *
 * @returns {Promise<void>} Resolves after state updates.
 */
async function loadCategoryTotals() {
  categoryLoading.value = true
  categoryError.value = ''
  try {
    const response = await fetchCategoryBreakdownTree({
      start_date: props.detailDate,
      end_date: props.detailDate,
    })
    if (response?.status !== 'success') {
      categoryRows.value = []
      categoryError.value = 'error'
      return
    }
    categoryRows.value = normalizeCategoryTotals(response?.data || [])
  } catch (err) {
    console.error('Error loading daily category breakdown:', err)
    categoryRows.value = []
    categoryError.value = 'error'
  } finally {
    categoryLoading.value = false
    await renderChart(categoryRows.value, averageRows.value)
  }
}

/**
 * Load average category totals for the active detail range.
 *
 * @returns {Promise<void>} Resolves after state updates.
 */
async function loadAverageProfile() {
  const dayCount = getInclusiveDayCount(props.minDetailDate, props.detailDate)
  if (dayCount <= 0) {
    averageRows.value = []
    await renderChart(categoryRows.value, averageRows.value)
    return
  }

  try {
    const response = await fetchCategoryBreakdownTree({
      start_date: props.minDetailDate,
      end_date: props.detailDate,
    })
    if (response?.status !== 'success') {
      averageRows.value = []
      return
    }
    const totals = normalizeCategoryTotals(response?.data || [])
    // Convert total spending into per-day averages for the overlay.
    averageRows.value = totals.map((row) => ({
      ...row,
      amount: row.amount / dayCount,
    }))
  } catch (err) {
    console.error('Error loading average spending profile:', err)
    averageRows.value = []
  } finally {
    await renderChart(categoryRows.value, averageRows.value)
  }
}

/**
 * Load the latest transactions for the selected detail date.
 *
 * @returns {Promise<void>} Resolves after state updates.
 */
async function loadTransactions() {
  transactionsLoading.value = true
  transactionsError.value = ''
  try {
    const response = await fetchTransactions({
      start_date: props.detailDate,
      end_date: props.detailDate,
      page_size: 6,
    })
    const items = Array.isArray(response?.transactions) ? response.transactions : []
    transactions.value = items
      .slice()
      .sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0))
      .slice(0, 6)
  } catch (err) {
    console.error('Error loading daily transactions:', err)
    transactions.value = []
    transactionsError.value = 'error'
  } finally {
    transactionsLoading.value = false
  }
}

/**
 * Load daily spending data in parallel.
 *
 * @returns {Promise<void>} Resolves after all data fetches.
 */
async function refreshData() {
  await Promise.allSettled([loadCategoryTotals(), loadTransactions()])
}

/**
 * Format a transaction date for display.
 *
 * @param {string} value - ISO date string.
 * @returns {string} Formatted date string.
 */
function formatTransactionDate(value) {
  const parsed = parseISODate(value)
  if (!parsed) {
    return 'Unknown date'
  }
  return parsed.toLocaleDateString(undefined, { month: 'short', day: '2-digit' })
}

/**
 * Build a display label for a transaction row.
 *
 * @param {Object} transaction - Transaction record.
 * @returns {string} Display name.
 */
function transactionLabel(transaction) {
  return (
    transaction?.merchant_name ||
    transaction?.name ||
    transaction?.description ||
    transaction?.original_description ||
    'Transaction'
  )
}

watch(
  [() => props.detailDate, () => props.minDetailDate],
  () => {
    refreshData()
    if (compareToAverage.value) {
      loadAverageProfile()
    } else {
      averageRows.value = []
    }
  },
  { immediate: true },
)

watch(compareToAverage, (enabled) => {
  if (enabled) {
    loadAverageProfile()
  } else {
    averageRows.value = []
    renderChart(categoryRows.value, averageRows.value)
  }
})

onUnmounted(() => {
  destroyChart()
})
</script>

<style scoped>
.daily-spending-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.panel-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.average-toggle {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.average-toggle input {
  accent-color: var(--color-accent-yellow);
}

.panel-title {
  margin: 0;
  font-size: 1rem;
  color: var(--color-accent-yellow);
}

.panel-subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.panel-content {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: 1rem;
}

.chart-card,
.transactions-card {
  position: relative;
  background: var(--color-bg-dark);
  border: 1px solid var(--divider);
  border-radius: 10px;
  padding: 0.75rem;
  min-height: 220px;
}

.chart-canvas {
  width: 100%;
  height: 180px;
}

.panel-state {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.panel-state-error {
  color: var(--color-accent-red);
}

.transactions-title {
  margin: 0 0 0.5rem;
  font-size: 0.85rem;
  color: var(--color-text-light);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.transactions-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.transaction-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
  border-bottom: 1px dashed var(--divider);
  padding-bottom: 0.5rem;
}

.transaction-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.transaction-meta {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.transaction-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-light);
}

.transaction-date {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.transaction-amount {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-text-light);
}

@media (max-width: 900px) {
  .panel-content {
    grid-template-columns: 1fr;
  }
}
</style>
