<!-- src/components/forecast/ForecastChart.vue -->
<template>
  <div class="chart-container">
    <div class="chart-header">
      <div class="chart-header-copy">
        <h2 class="chart-title">Forecast vs Actuals ({{ viewType }})</h2>
        <details class="chart-methodology" :open="isMethodologyOpen">
          <summary class="chart-methodology-summary" @click.prevent="toggleMethodology">
            How this forecast is calculated
          </summary>
          <p class="chart-methodology-body">
            {{ methodologyCopy }}
          </p>
        </details>
      </div>
      <button @click="toggleView" class="toggle-button">
        Switch to {{ viewType === 'Month' ? 'Year' : 'Month' }}
      </button>
    </div>
    <div v-if="!hasData" class="chart-empty">Forecast chart data is not available yet.</div>
    <canvas v-else ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const props = defineProps({
  timeline: {
    type: Array,
    default: () => [],
  },
  realizedHistory: {
    type: Array,
    default: () => [],
  },
  viewType: {
    type: String,
    default: 'Month',
  },
  graphMode: {
    type: String,
    default: 'combined',
  },
  computeMeta: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:viewType'])
const chartCanvas = ref(null)
const isMethodologyOpen = ref(false)
let chartInstance = null

const labels = computed(() => {
  const historyLabels = props.realizedHistory.map((point) => point.label)
  const forecastLabels = props.timeline.map((point) => point.label)
  return [...historyLabels, ...forecastLabels]
})
const hasData = computed(() => labels.value.length > 0)

/**
 * Summarize the compute controls shown above the chart for quick reference.
 */
const methodologyCopy = computed(() => {
  const lookbackDays = Number(props.computeMeta?.lookbackDays ?? 0)
  const movingAverageWindow = Number(props.computeMeta?.movingAverageWindow ?? 0)
  const normalizeState = props.computeMeta?.normalize
    ? 'Normalization is on'
    : 'Normalization is off'
  const autoDetectedCount = Number(props.computeMeta?.autoDetectedAdjustmentCount ?? 0)
  const autoDetectedCopy = props.computeMeta?.includesAutoDetectedAdjustments
    ? `Auto-detected adjustments are included${autoDetectedCount > 0 ? ` (${autoDetectedCount} detected)` : ''}.`
    : 'Auto-detected adjustments are not included.'

  return `It uses the latest ${lookbackDays || 'available'} days of realized history, applies a ${movingAverageWindow || 'current'}-day moving average, and renders in ${props.graphMode} mode. ${normalizeState}. ${autoDetectedCopy}`
})

function toggleView() {
  emit('update:viewType', props.viewType === 'Month' ? 'Year' : 'Month')
}

/**
 * Keep the methodology copy compact until the user requests it.
 */
function toggleMethodology() {
  isMethodologyOpen.value = !isMethodologyOpen.value
}

function destroyChart() {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
}

function renderChart() {
  if (!chartCanvas.value) return
  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return
  destroyChart()

  const historyData = props.realizedHistory.map((point) => point.balance)
  const forecastData = props.timeline.map((point) => point.forecast_balance)
  const historicalOnly = props.graphMode === 'historical'
  const forecastOnly = props.graphMode === 'forecast'
  const datasets = [
    {
      label: 'Historical',
      data:
        historicalOnly || props.graphMode === 'combined'
          ? [...historyData, ...new Array(forecastData.length).fill(null)]
          : [],
      borderColor: '#10B981',
      tension: 0.3,
      borderDash: [],
    },
    {
      label: 'Forecast',
      data:
        forecastOnly || props.graphMode === 'combined'
          ? [...new Array(historyData.length).fill(null), ...forecastData]
          : [],
      borderColor: '#3B82F6',
      tension: 0.3,
      borderDash: [5, 5],
    },
  ]

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: { labels: labels.value, datasets },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      scales: { y: { beginAtZero: false } },
    },
  })
}

onMounted(renderChart)
onBeforeUnmount(destroyChart)
watch(() => [props.timeline, props.realizedHistory, props.graphMode], renderChart, { deep: true })
</script>

<style scoped>
@reference "../../assets/css/main.css";
.chart-container {
  background-color: var(--surface);
  color: var(--theme-fg);
  border: 1px solid var(--divider);
  border-radius: 0.5rem;
  padding: 1rem;
}
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}
.chart-header-copy {
  display: grid;
  gap: 0.35rem;
}
.chart-title {
  font-size: 1.125rem;
  font-weight: 600;
}
.chart-methodology {
  font-size: 0.8rem;
  color: var(--text-muted);
}
.chart-methodology-summary {
  cursor: pointer;
  list-style: none;
  font-weight: 500;
}
.chart-methodology-summary::-webkit-details-marker {
  display: none;
}
.chart-methodology-summary::before {
  content: 'ⓘ';
  margin-right: 0.35rem;
}
.chart-methodology-body {
  margin-top: 0.35rem;
  max-width: 36rem;
  line-height: 1.45;
}
.toggle-button {
  font-size: 0.875rem;
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--divider);
  border-radius: 0.375rem;
  background-color: var(--input-bg);
  color: var(--theme-fg);
  cursor: pointer;
  transition: background-color 0.2s ease;
}
.toggle-button:hover {
  background-color: var(--hover-bg);
}
.chart-empty {
  padding: 1.5rem;
  text-align: center;
  font-size: 0.9rem;
  color: var(--text-muted);
}
</style>
