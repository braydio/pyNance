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
        Switch to {{ props.viewType === 'Month' ? 'Year' : 'Month' }}
      </button>
    </div>

    <div v-if="!hasData" class="chart-empty">Forecast chart data is not available yet.</div>
    <canvas v-else ref="chartCanvas"></canvas>
  </div>
</template>

<script setup lang="ts">
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

type ForecastAspectKey = 'balances' | 'realized_income' | 'manual_adjustments' | 'spending' | 'debt'

const ASPECT_META: Record<ForecastAspectKey, { label: string; subtitle: string }> = {
  balances: {
    label: 'Balances',
    subtitle: 'Historical balances are overlaid against projected balances.',
  },
  realized_income: {
    label: 'Realized income',
    subtitle: 'Realized income shows the daily values used for the forecast baseline.',
  },
  manual_adjustments: {
    label: 'Manual adjustments',
    subtitle: 'Manual adjustments isolate user-entered forecast changes.',
  },
  spending: {
    label: 'Spending',
    subtitle: 'Spending shows projected outflows from the forecast cashflow model.',
  },
  debt: {
    label: 'Debt composition',
    subtitle: 'Debt total is rendered alongside new-spending and interest-growth components.',
  },
}

const props = withDefaults(
  defineProps<{
    timeline?: ForecastTimelinePoint[]
    realizedHistory?: RealizedHistoryPoint[]
    viewType?: ForecastViewType
    graphMode?: ForecastGraphMode
    selectedAspect?: ForecastAspectKey
    series?: ForecastSeriesMap
    cashflows?: Array<Record<string, unknown>>
    assetBalance?: number
    liabilityBalance?: number
    netBalance?: number
    computeMeta?: ForecastComputeMeta
  }>(),
  {
    timeline: () => [],
    realizedHistory: () => [],
    viewType: 'Month',
    graphMode: 'combined',
    selectedAspect: 'balances',
    series: () => ({}),
    cashflows: () => [],
    assetBalance: 0,
    liabilityBalance: 0,
    netBalance: 0,
    computeMeta: () => ({}),
  },
)

const emit = defineEmits<{
  (event: 'update:viewType', value: ForecastViewType): void
}>()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
const isMethodologyOpen = ref(false)
let chartInstance: Chart | null = null

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
const chartMeta = computed(() => ASPECT_META[props.selectedAspect] || ASPECT_META.balances)
const chartTitle = computed(() => `${props.viewType} · ${chartMeta.value.label}`)
const chartSubtitle = computed(() => chartMeta.value.subtitle)

const methodologyCopy = computed(() => {
  const lookbackDays = Number(props.computeMeta?.lookbackDays ?? 0)
  const movingAverageWindow = Number(props.computeMeta?.movingAverageWindow ?? 0)
  const normalizeState = props.computeMeta?.normalize
    ? 'Normalization is on.'
    : 'Normalization is off.'
  const autoDetectedCount = Number(props.computeMeta?.autoDetectedAdjustmentCount ?? 0)
  const autoDetectedCopy = props.computeMeta?.includesAutoDetectedAdjustments
    ? `Auto-detected adjustments are included${autoDetectedCount > 0 ? ` (${autoDetectedCount} detected)` : ''}.`
    : 'Auto-detected adjustments are not included.'

  return `It uses the latest ${lookbackDays || 'available'} days of realized history, applies a ${movingAverageWindow || 'current'}-day moving average, renders in ${props.graphMode} mode, and keeps debt growth split between new spending and interest when those series are available. ${normalizeState} ${autoDetectedCopy}`
})

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

function buildBalanceDatasets(): ChartDataset<'line', Array<number | null>>[] {
  const datasets: ChartDataset<'line', Array<number | null>>[] = []
  const historicalOnly = props.graphMode === 'historical'
  const forecastOnly = props.graphMode === 'forecast'

  if (!forecastOnly) {
    datasets.push({
      type: 'line',
      label: 'Historical balance',
      data: alignSeriesValues(
        props.realizedHistory.map((point) => ({
          date: point.date || point.label,
          label: point.label,
          value: point.balance,
        })),
      ),
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
      data: alignSeriesValues(
        props.timeline.map((point) => ({
          date: point.date || point.label,
          label: point.label,
          value: point.forecast_balance,
        })),
      ),
      borderColor: '#3B82F6',
      backgroundColor: 'rgba(59, 130, 246, 0.15)',
      yAxisID: 'yBalance',
      tension: 0.3,
      borderDash: [5, 5],
      spanGaps: true,
    })
  }

  return datasets
}

function buildSingleSeriesDataset(
  seriesKey: string,
  config: {
    color: string
    type: 'line' | 'bar'
    yAxisID: 'yBalance' | 'yFlow'
    borderDash?: number[]
  },
): ChartDataset<'line' | 'bar', Array<number | null>>[] {
  const entry = props.series?.[seriesKey]
  if (!entry || entry.points.length === 0) {
    return []
  }

  return [
    {
      type: config.type,
      label: entry.label,
      data: alignSeriesValues(entry.points),
      borderColor: config.color,
      backgroundColor: `${config.color}${config.type === 'bar' ? '66' : '22'}`,
      yAxisID: config.yAxisID,
      tension: config.type === 'line' ? 0.25 : 0,
      borderDash: config.borderDash ?? [],
      spanGaps: true,
    },
  ]
}

function buildDebtDatasets(): ChartDataset<'line' | 'bar', Array<number | null>>[] {
  const totalEntry = props.series?.debt_totals
  const interestEntry = props.series?.debt_interest
  const newSpendingEntry = props.series?.debt_new_spending

  if (totalEntry || interestEntry || newSpendingEntry) {
    const datasets: ChartDataset<'line' | 'bar', Array<number | null>>[] = []
    if (totalEntry) {
      datasets.push({
        type: 'line',
        label: totalEntry.label,
        data: alignSeriesValues(totalEntry.points),
        borderColor: '#F59E0B',
        backgroundColor: '#F59E0B22',
        yAxisID: 'yBalance',
        tension: 0.25,
        borderDash: [3, 3],
        spanGaps: true,
      })
    }
    if (interestEntry) {
      datasets.push({
        type: 'bar',
        label: interestEntry.label,
        data: alignSeriesValues(interestEntry.points),
        borderColor: '#EF4444',
        backgroundColor: '#EF444466',
        yAxisID: 'yFlow',
        tension: 0,
        spanGaps: true,
      })
    }
    if (newSpendingEntry) {
      datasets.push({
        type: 'bar',
        label: newSpendingEntry.label,
        data: alignSeriesValues(newSpendingEntry.points),
        borderColor: '#8B5CF6',
        backgroundColor: '#8B5CF666',
        yAxisID: 'yFlow',
        tension: 0,
        spanGaps: true,
      })
    }
    return datasets
  }

  if (!labels.value.length) {
    return []
  }

  return [
    {
      type: 'line',
      label: 'Assets',
      data: labels.value.map(() => props.assetBalance),
      borderColor: '#10B981',
      backgroundColor: '#10B98122',
      yAxisID: 'yBalance',
      tension: 0.2,
      spanGaps: true,
    },
    {
      type: 'line',
      label: 'Liabilities',
      data: labels.value.map(() => props.liabilityBalance),
      borderColor: '#F59E0B',
      backgroundColor: '#F59E0B22',
      yAxisID: 'yBalance',
      tension: 0.2,
      spanGaps: true,
    },
    {
      type: 'line',
      label: 'Net balance',
      data: labels.value.map(() => props.netBalance),
      borderColor: '#3B82F6',
      backgroundColor: '#3B82F622',
      yAxisID: 'yBalance',
      tension: 0.2,
      spanGaps: true,
    },
  ]
}

const chartDatasets = computed<ChartDataset<'line' | 'bar', Array<number | null>>[]>(() => {
  switch (props.selectedAspect) {
    case 'realized_income':
      return buildSingleSeriesDataset('realized_income', {
        color: '#16A34A',
        type: 'bar',
        yAxisID: 'yFlow',
      })
    case 'manual_adjustments':
      return buildSingleSeriesDataset('manual_adjustments', {
        color: '#8B5CF6',
        type: 'bar',
        yAxisID: 'yFlow',
      })
    case 'spending':
      return buildSingleSeriesDataset('spending', {
        color: '#DC2626',
        type: 'bar',
        yAxisID: 'yFlow',
      })
    case 'debt':
      return buildDebtDatasets()
    case 'balances':
    default:
      return buildBalanceDatasets()
  }
})

const hasData = computed(
  () =>
    labels.value.length > 0 &&
    chartDatasets.value.some((dataset) => dataset.data.some((value) => value !== null)),
)

function toggleView() {
  emit('update:viewType', props.viewType === 'Month' ? 'Year' : 'Month')
}

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
      maintainAspectRatio: false,
      scales: {
        yBalance: {
          type: 'linear',
          position: 'left',
        },
        yFlow: {
          type: 'linear',
          position: 'right',
          grid: {
            drawOnChartArea: false,
          },
        },
      },
    },
  }
  chartInstance = new Chart(ctx, configuration)
}

watch(
  () => [
    props.timeline,
    props.realizedHistory,
    props.graphMode,
    props.series,
    props.selectedAspect,
  ],
  renderChart,
  { deep: true },
)

onMounted(() => {
  renderChart()
})

onBeforeUnmount(() => {
  destroyChart()
})
</script>

<style scoped>
.chart-container {
  min-height: 24rem;
}

.chart-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.chart-header-copy {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.chart-title {
  font-size: 1.125rem;
  font-weight: 600;
}

.chart-subtitle,
.chart-methodology-body,
.chart-empty {
  color: #4b5563;
}

.chart-methodology-summary {
  cursor: pointer;
  font-weight: 500;
}

.toggle-button {
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
}

canvas {
  min-height: 20rem;
}
</style>
