<template>
  <div class="chart-container">
    <div class="chart-header">
      <div class="chart-header-copy">
        <h2 class="chart-title">{{ chartTitle }}</h2>
        <p class="chart-subtitle">{{ chartSubtitle }}</p>

        <details class="chart-methodology" :open="isMethodologyOpen">
          <summary class="chart-methodology-summary" @click.prevent="toggleMethodology">
            How this forecast is calculated
          </summary>
          <p class="chart-methodology-body">
            {{ methodologyCopy }}
          </p>
        </details>
      </div>

      <button type="button" class="toggle-button" @click="toggleView">
        Switch to {{ viewType === 'Month' ? 'Year' : 'Month' }}
      </button>
    </div>

    <div v-if="!hasData" class="chart-empty">Forecast chart data is not available yet.</div>
    <canvas v-else ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Filler,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js'

Chart.register(
  LineController,
  LineElement,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Legend,
  Tooltip,
  Filler,
)

const ASPECT_META = {
  balances: {
    label: 'Balances',
    subtitle: 'Historical balances are overlaid against projected balances.',
  },
  realized_income: {
    label: 'Realized income',
    subtitle:
      'Income points come directly from the backend series used for auto-calculation context.',
  },
  manual_adjustments: {
    label: 'Manual adjustments',
    subtitle: 'Manual entries come directly from the backend adjustment series.',
  },
  spending: {
    label: 'Spending',
    subtitle: 'Spending points use the backend-provided daily outflow totals.',
  },
  debt_totals: {
    label: 'Debt totals',
    subtitle: 'Debt totals use the backend-provided liability series across the forecast horizon.',
  },
}

const ASPECT_STYLES = {
  realized_income: { color: '#16A34A', type: 'bar', axis: 'yFlow' },
  manual_adjustments: { color: '#7C3AED', type: 'bar', axis: 'yFlow' },
  spending: { color: '#DC2626', type: 'bar', axis: 'yFlow' },
  debt_totals: { color: '#F59E0B', type: 'line', axis: 'yBalance' },
}

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
  selectedAspect: {
    type: String,
    default: 'balances',
  },
  series: {
    type: Object,
    default: () => ({}),
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

const activeSeries = computed(() => {
  if (props.selectedAspect === 'balances') {
    return null
  }
  return props.series?.[props.selectedAspect] ?? null
})

const axisDates = computed(() => {
  const dateSet = new Set()

  props.realizedHistory.forEach((point) => dateSet.add(point.date || point.label))
  props.timeline.forEach((point) => dateSet.add(point.date || point.label))
  activeSeries.value?.points.forEach((point) => dateSet.add(point.date || point.label))

  return Array.from(dateSet).sort((left, right) => left.localeCompare(right))
})
const labels = computed(() => axisDates.value)
const chartMeta = computed(() => ASPECT_META[props.selectedAspect] || ASPECT_META.balances)
const chartTitle = computed(() => `${props.viewType} · ${chartMeta.value.label}`)
const chartSubtitle = computed(() => chartMeta.value.subtitle)

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

const chartDatasets = computed(() => {
  if (props.selectedAspect === 'balances') {
    return buildBalanceDatasets()
  }

  const seriesEntry = activeSeries.value
  if (!seriesEntry) {
    return []
  }

  const style = ASPECT_STYLES[seriesEntry.id]
  return [
    {
      type: style.type,
      label: seriesEntry.label,
      data: alignSeriesValues(seriesEntry.points),
      borderColor: style.color,
      backgroundColor: toRgba(style.color, style.type === 'bar' ? 0.45 : 0.15),
      yAxisID: style.axis,
      tension: style.type === 'line' ? 0.25 : 0,
      borderDash: seriesEntry.id === 'debt_totals' ? [4, 4] : [],
      spanGaps: true,
    },
  ]
})

const hasData = computed(
  () =>
    labels.value.length > 0 &&
    chartDatasets.value.some((dataset) => dataset.data.some((value) => value !== null)),
)

/**
 * Emit the opposite timeframe while leaving the active aspect untouched.
 */
function toggleView() {
  emit('update:viewType', props.viewType === 'Month' ? 'Year' : 'Month')
}

/**
 * Keep the methodology copy compact until the user requests it.
 */
function toggleMethodology() {
  isMethodologyOpen.value = !isMethodologyOpen.value
}

/**
 * Tear down any prior Chart.js instance before a re-render.
 */
function destroyChart() {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
}

/**
 * Align a date-keyed point collection to the chart axis, inserting null gaps.
 */
function alignSeriesValues(points) {
  const valuesByDate = new Map()
  points.forEach((point) => {
    const axisDate = point.date || point.label
    if (axisDate) {
      valuesByDate.set(axisDate, Number(point.value ?? 0))
    }
  })

  return axisDates.value.map((axisDate) => valuesByDate.get(axisDate) ?? null)
}

/**
 * Build the balance overlay datasets from realized history and projected balances.
 */
function buildBalanceDatasets() {
  const datasets = []
  const historicalOnly = props.graphMode === 'historical'
  const forecastOnly = props.graphMode === 'forecast'

  const historicalDataset = alignSeriesValues(
    props.realizedHistory.map((point) => ({
      date: point.date || point.label,
      label: point.label,
      value: point.balance,
    })),
  )
  const forecastDataset = alignSeriesValues(
    props.timeline.map((point) => ({
      date: point.date || point.label,
      label: point.label,
      value: point.forecast_balance,
    })),
  )

  if (!forecastOnly) {
    datasets.push({
      type: 'line',
      label: 'Historical balance',
      data: historicalDataset,
      borderColor: '#10B981',
      backgroundColor: toRgba('#10B981', 0.15),
      yAxisID: 'yBalance',
      tension: 0.3,
      spanGaps: true,
    })
  }

  if (!historicalOnly) {
    datasets.push({
      type: 'line',
      label: 'Forecast balance',
      data: forecastDataset,
      borderColor: '#3B82F6',
      backgroundColor: toRgba('#3B82F6', 0.15),
      yAxisID: 'yBalance',
      tension: 0.3,
      borderDash: [5, 5],
      spanGaps: true,
    })
  }

  return datasets
}

/**
 * Convert a hex color into an rgba string so datasets stay readable.
 */
function toRgba(hex, alpha) {
  const sanitized = hex.replace('#', '')
  const chunkSize = sanitized.length === 3 ? 1 : 2
  const channels = sanitized.match(new RegExp(`.{1,${chunkSize}}`, 'g')) || []
  const [red, green, blue] = channels.map((segment) =>
    parseInt(chunkSize === 1 ? `${segment}${segment}` : segment, 16),
  )
  return `rgba(${red || 0}, ${green || 0}, ${blue || 0}, ${alpha})`
}

/**
 * Render the chart with the currently selected aspect datasets.
 */
function renderChart() {
  if (!chartCanvas.value || !hasData.value) {
    destroyChart()
    return
  }

  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) {
    return
  }

  destroyChart()
  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.value,
      datasets: chartDatasets.value,
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      scales: {
        yBalance: {
          type: 'linear',
          position: 'left',
          beginAtZero: false,
          title: {
            display: true,
            text: 'Balance',
          },
        },
        yFlow: {
          type: 'linear',
          position: 'right',
          grid: { drawOnChartArea: false },
          title: {
            display: true,
            text: 'Daily amount',
          },
        },
      },
      plugins: {
        legend: {
          display: chartDatasets.value.length > 1,
        },
      },
    },
  })
}

onMounted(renderChart)
onBeforeUnmount(destroyChart)
watch(
  () => [
    props.timeline,
    props.realizedHistory,
    props.graphMode,
    props.selectedAspect,
    props.series,
  ],
  renderChart,
  { deep: true },
)
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
.chart-subtitle {
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: var(--text-muted);
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
