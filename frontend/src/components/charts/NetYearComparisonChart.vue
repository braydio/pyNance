<template>
  <div class="chart-container card">
    <h2 class="heading-md">{{ chartTypeLabel }} Year Comparison</h2>
    <div class="toggle-group" role="group" aria-label="Chart type">
      <button
        v-for="type in chartTypes"
        :key="type.value"
        type="button"
        class="btn btn-pill"
        :class="{ active: activeChart === type.value }"
        :aria-pressed="activeChart === type.value ? 'true' : 'false'"
        @click="setChartType(type.value)"
      >
        {{ type.label }}
      </button>
    </div>
    <p v-if="loading" class="chart-state" role="status" data-testid="year-chart-loading">
      Loading history…
    </p>
    <div v-else-if="loadError" class="chart-state" role="alert" data-testid="year-chart-error">
      <p>Unable to load balance history.</p>
      <button type="button" class="btn btn-sm" @click="fetchData">Retry</button>
    </div>
    <p v-else-if="!chartData.length" class="chart-state" data-testid="year-chart-empty">
      No balance history yet. Link an account and let it sync to compare years.
    </p>
    <div v-show="!loading && !loadError && chartData.length" class="chart-wrapper">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import api from '@/services/api.js'
import { ref, onMounted, nextTick } from 'vue'
import { Chart } from 'chart.js/auto'

function getStyle(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

function withAlpha(color, alpha) {
  const c = color.trim()
  if (c.startsWith('#')) {
    const bigint = parseInt(c.slice(1), 16)
    const r = (bigint >> 16) & 255
    const g = (bigint >> 8) & 255
    const b = bigint & 255
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }
  return color
}

const chartCanvas = ref(null)
const chartInstance = ref(null)
const chartData = ref([])
const loading = ref(true)
const loadError = ref(false)
const activeChart = ref('assets')
const chartTypeLabel = ref('Assets')

const MONTH_LABELS = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
]
const currentYear = new Date().getFullYear()
const previousYear = currentYear - 1

const chartTypes = [
  { label: 'Assets', value: 'assets' },
  { label: 'Liabilities', value: 'liabilities' },
  { label: 'Net Worth', value: 'netWorth' },
]

function formatCurrency(val) {
  const num = Number(val || 0)
  return num < 0 ? `($${Math.abs(num).toLocaleString()})` : `$${num.toLocaleString()}`
}

function normalisePoint(point) {
  if (!point || !point.date) return null

  const [dateOnly] = point.date.split('T')

  return {
    date: dateOnly,
    assets: Number(point.assets ?? 0),
    liabilities: Number(point.liabilities ?? 0),
    // ``net_assets`` is the legacy backend key – ensure we expose a ``netWorth``
    // property so the chart toggles render as expected regardless of payload
    // shape.
    netWorth: Number(point.netWorth ?? point.net_assets ?? point.net ?? point.net_worth ?? 0),
  }
}

function parseByType(year, key) {
  const result = new Array(12).fill(null)
  chartData.value.forEach((d) => {
    const [y, m] = d.date.split('-').map(Number)
    if (y === year) result[m - 1] = d[key]
  })
  return result
}

async function fetchData() {
  loading.value = true
  loadError.value = false
  try {
    const data = await api.fetchNetAssets()
    const rawPoints = Array.isArray(data?.data) ? data.data : []
    chartData.value = rawPoints.map((point) => normalisePoint(point)).filter(Boolean)
    loading.value = false
    await nextTick()
    buildChart()
  } catch (e) {
    console.error('Chart fetch failed:', e)
    loadError.value = true
    loading.value = false
  }
}

function buildChart() {
  if (!chartData.value.length) return
  if (chartInstance.value) chartInstance.value.destroy()

  const canvasEl = chartCanvas.value
  if (!canvasEl) return
  const ctx = canvasEl.getContext('2d')
  if (!ctx) return

  chartInstance.value = new Chart(ctx, {
    type: 'line',
    data: {
      labels: MONTH_LABELS,
      datasets: [
        {
          label: `${chartTypeLabel.value} (${previousYear})`,
          data: parseByType(previousYear, activeChart.value),
          borderColor: getStyle('--color-accent-cyan'),
          backgroundColor: withAlpha(getStyle('--color-accent-cyan'), 0.3),
          fill: true,
          tension: 0.25,
        },
        {
          label: `${chartTypeLabel.value} (${currentYear})`,
          data: parseByType(currentYear, activeChart.value),
          borderColor: getStyle('--color-accent-yellow'),
          backgroundColor: withAlpha(getStyle('--color-accent-yellow'), 0.3),
          fill: true,
          tension: 0.25,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: {
            color: getStyle('--color-text-muted'),
            boxWidth: 14,
            usePointStyle: true,
          },
        },
        tooltip: {
          enabled: true,
          backgroundColor: getStyle('--theme-bg'),
          borderColor: getStyle('--divider'),
          borderWidth: 1,
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`,
          },
        },
      },
      scales: {
        x: {
          ticks: { color: getStyle('--color-text-muted') },
          grid: { color: getStyle('--divider') },
        },
        y: {
          ticks: {
            color: getStyle('--color-text-muted'),
            callback: formatCurrency,
          },
          grid: { color: getStyle('--divider') },
        },
      },
    },
  })
}

function setChartType(type) {
  activeChart.value = type
  chartTypeLabel.value = chartTypes.find((t) => t.value === type).label
  buildChart()
}

onMounted(fetchData)
</script>

<style scoped>
@reference "../../assets/css/main.css";
.chart-state {
  padding: 1.5rem 0;
  text-align: center;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.chart-container {
  width: 100%;
  padding: 0.75rem;
  background-color: var(--color-bg-secondary);
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow);
}

.toggle-group {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.toggle-group .btn.active {
  background: var(--color-accent-cyan);
  color: var(--color-bg-dark);
  box-shadow: 0 0 6px var(--color-accent-cyan);
}

.chart-wrapper {
  position: relative;
  height: 300px;
  width: 100%;
}

canvas {
  width: 100% !important;
  height: 100% !important;
}
</style>
