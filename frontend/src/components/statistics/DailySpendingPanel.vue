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
})

const chartCanvas = ref(null)
const chartInstance = ref(null)
const categoryRows = ref([])
const categoryLoading = ref(false)
const categoryError = ref('')
const transactions = ref([])
const transactionsLoading = ref(false)
const transactionsError = ref('')

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
 * Render the stacked bar chart for today's category totals.
 *
 * @param {Array<{ label: string, amount: number }>} rows - Category totals.
 * @returns {Promise<void>} Resolves after chart rendering completes.
 */
async function renderChart(rows) {
  await nextTick()
  const canvasEl = chartCanvas.value
  if (!canvasEl) {
    return
  }
  destroyChart()
  if (!rows.length) {
    return
  }
  const ctx = canvasEl.getContext('2d')
  if (!ctx) {
    return
  }

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Today'],
      datasets: rows.map((row, idx) => ({
        label: row.label,
        data: [row.amount],
        backgroundColor: getAccentColor(idx),
        borderRadius: 8,
        borderSkipped: false,
        stack: 'today-stack',
      })),
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
    await renderChart(categoryRows.value)
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
  () => props.detailDate,
  () => {
    refreshData()
  },
  { immediate: true },
)

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
