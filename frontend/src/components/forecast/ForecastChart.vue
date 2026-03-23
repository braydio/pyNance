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
      <button class="toggle-button" @click="toggleView">
        Switch to {{ viewType === 'Month' ? 'Year' : 'Month' }}
      </button>
    </div>
    <div v-if="!hasData" class="chart-empty">Forecast chart data is not available yet.</div>
    <canvas v-else ref="chartCanvas"></canvas>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Chart,
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
  type ChartConfiguration,
  type ChartDataset,
} from 'chart.js'
import type {
  ForecastGraphMode,
  ForecastSeriesMap,
  ForecastTimelinePoint,
  ForecastViewType,
} from '@/composables/useForecastData'

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

type RealizedHistoryPoint = {
  date?: string
  label: string
  balance: number
}

type ForecastComputeMeta = {
  lookbackDays?: number
  movingAverageWindow?: number
  normalize?: boolean
  includesAutoDetectedAdjustments?: boolean
  autoDetectedAdjustmentCount?: number
}

const props = withDefaults(
  defineProps<{
    timeline?: ForecastTimelinePoint[]
    realizedHistory?: RealizedHistoryPoint[]
    viewType?: ForecastViewType
    graphMode?: ForecastGraphMode
    series?: ForecastSeriesMap
    computeMeta?: ForecastComputeMeta
  }>(),
  {
    timeline: () => [],
    realizedHistory: () => [],
    viewType: 'Month',
    graphMode: 'combined',
    series: () => ({}),
    computeMeta: () => ({}),
  },
)

const emit = defineEmits<{
  (event: 'update:viewType', value: ForecastViewType): void
}>()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
const isMethodologyOpen = ref(false)
let chartInstance: Chart | null = null

/**
 * Normalize any series point list into a sorted date-keyed axis.
 */
const axisDates = computed(() => {
  const dateSet = new Set<string>()

  props.realizedHistory.forEach((point) => {
    dateSet.add(point.date || point.label)
  })
  props.timeline.forEach((point) => {
    dateSet.add(point.date || point.label)
  })
  Object.values(props.series || {}).forEach((entry) => {
    entry.points.forEach((point) => {
      dateSet.add(point.date || point.label)
    })
  })

  return Array.from(dateSet).sort((left, right) => left.localeCompare(right))
})

const labels = computed(() => axisDates.value)
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

/**
 * Align a date-keyed point collection to the chart axis, inserting null gaps.
 */
function alignSeriesValues(
  points: Array<{ date?: string; label: string; value: number | null | undefined }>,
): Array<number | null> {
  const valuesByDate = new Map<string, number>()
  points.forEach((point) => {
    const axisDate = point.date || point.label
    if (axisDate) {
      valuesByDate.set(axisDate, Number(point.value ?? 0))
    }
  })

  return axisDates.value.map((axisDate) => valuesByDate.get(axisDate) ?? null)
}

/**
 * Build balance and aspect datasets from typed backend series.
 */
const chartDatasets = computed(() => {
  const historicalOnly = props.graphMode === 'historical'
  const forecastOnly = props.graphMode === 'forecast'

  const datasets: ChartDataset<'line' | 'bar', Array<number | null>>[] = []

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
      backgroundColor: 'rgba(16, 185, 129, 0.15)',
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
      backgroundColor: 'rgba(59, 130, 246, 0.15)',
      yAxisID: 'yBalance',
      tension: 0.3,
      borderDash: [5, 5],
      spanGaps: true,
    })
  }

  const aspectConfigs: Array<{
    key: keyof ForecastSeriesMap | string
    color: string
    type: 'line' | 'bar'
    yAxisID: 'yBalance' | 'yFlow'
  }> = [
    { key: 'realized_income', color: '#16A34A', type: 'bar', yAxisID: 'yFlow' },
    { key: 'manual_adjustments', color: '#8B5CF6', type: 'bar', yAxisID: 'yFlow' },
    { key: 'spending', color: '#DC2626', type: 'bar', yAxisID: 'yFlow' },
    { key: 'debt_totals', color: '#F59E0B', type: 'line', yAxisID: 'yBalance' },
  ]

  aspectConfigs.forEach((config) => {
    const entry = props.series?.[config.key]
    if (!entry || !entry.points.length) {
      return
    }

    datasets.push({
      type: config.type,
      label: entry.label,
      data: alignSeriesValues(entry.points),
      borderColor: config.color,
      backgroundColor: `${config.color}${config.type === 'bar' ? '66' : '22'}`,
      yAxisID: config.yAxisID,
      tension: config.type === 'line' ? 0.25 : 0,
      borderDash: entry.id === 'debt_totals' ? [3, 3] : [],
      spanGaps: true,
    })
  })

  return datasets
})

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

  const configuration: ChartConfiguration<'line' | 'bar', Array<number | null>, string> = {
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
    },
  }

  chartInstance = new Chart(ctx, configuration)
}

onMounted(renderChart)
onBeforeUnmount(destroyChart)
watch(() => [props.timeline, props.realizedHistory, props.graphMode, props.series], renderChart, {
  deep: true,
})
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
