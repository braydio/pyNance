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

      <div class="forecast-range-options" role="group" aria-label="Forecast horizon">
        <button
          v-for="option in forecastRanges"
          :key="option.value"
          type="button"
          class="toggle-button"
          :class="{ active: viewType === option.value }"
          :aria-pressed="viewType === option.value"
          @click="emit('update:viewType', option.value)"
        >{{ option.label }}</button>
      </div>
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
  debt: {
    label: 'Debt composition',
    subtitle:
      'Debt composition uses the backend-provided liability totals across the forecast horizon.',
  },
}

const ASPECT_STYLES = {
  realized_income: { color: '#16A34A', type: 'bar', axis: 'yFlow' },
  manual_adjustments: { color: '#7C3AED', type: 'bar', axis: 'yFlow' },
  spending: { color: '#DC2626', type: 'bar', axis: 'yFlow' },
  debt_totals: { color: '#F59E0B', type: 'line', axis: 'yBalance' },
  debt_interest: { color: '#F97316', type: 'bar', axis: 'yFlow' },
  debt_new_spending: { color: '#EF4444', type: 'bar', axis: 'yFlow' },
}
const ASPECT_SERIES_ID_BY_SELECTION = {
  realized_income: 'realized_income',
  manual_adjustments: 'manual_adjustments',
  spending: 'spending',
  debt: 'debt_totals',
}
const DEBT_COMPONENT_SERIES_IDS = ['debt_interest', 'debt_new_spending']

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
  modelVersion: {
    type: String,
    default: 'v1',
  },
  scenarioLines: {
    type: Array,
    default: () => [],
  },
})

const isV2 = computed(() => props.modelVersion === 'v2')
const hasBands = computed(() =>
  props.timeline.some((point) => point.p10 !== undefined && point.p90 !== undefined),
)

const emit = defineEmits(['update:viewType'])

const chartCanvas = ref(null)
const isMethodologyOpen = ref(false)
let chartInstance = null

const activeSeries = computed(() => {
  if (props.selectedAspect === 'balances') {
    return null
  }
  const seriesId = ASPECT_SERIES_ID_BY_SELECTION[props.selectedAspect]
  return props.series?.[seriesId] ?? null
})
const activeDebtComponentSeries = computed(() =>
  DEBT_COMPONENT_SERIES_IDS.map((seriesId) => props.series?.[seriesId]).filter(
    (seriesEntry) => seriesEntry && Array.isArray(seriesEntry.points),
  ),
)

const axisDates = computed(() => {
  const dateSet = new Set()

  props.realizedHistory.forEach((point) => dateSet.add(point.date || point.label))
  props.timeline.forEach((point) => dateSet.add(point.date || point.label))
  activeSeries.value?.points.forEach((point) => dateSet.add(point.date || point.label))
  activeDebtComponentSeries.value.forEach((seriesEntry) => {
    seriesEntry.points.forEach((point) => dateSet.add(point.date || point.label))
  })

  return Array.from(dateSet).sort((left, right) => left.localeCompare(right))
})
const labels = computed(() => axisDates.value)
const chartMeta = computed(() => ASPECT_META[props.selectedAspect] || ASPECT_META.balances)
const chartTitle = computed(() => `${props.viewType} · ${chartMeta.value.label}`)
const chartSubtitle = computed(() =>
  isV2.value && props.selectedAspect === 'balances'
    ? hasBands.value
      ? 'Projected liquid cash (checking, savings and cash). The shaded band is the simulated P10-P90 range; lower means less cash.'
      : 'Projected liquid cash (checking, savings and cash) from dated bills, paychecks and typical spending.'
    : chartMeta.value.subtitle,
)

/**
 * Summarize the compute controls shown above the chart for quick reference.
 */
const methodologyCopy = computed(() => {
  if (isV2.value) {
    return "Starts from today's cash and applies each detected bill and paycheck on its expected date, plus an estimate of everyday spending from your recent history. Debt and investments are shown separately and are not part of this cash line. Ranges come from a simulation of your own past variability and are estimates, not guarantees."
  }
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
  return buildAspectDatasets()
})

const hasData = computed(
  () =>
    labels.value.length > 0 &&
    chartDatasets.value.some((dataset) => dataset.data.some((value) => value !== null)),
)

const forecastRanges = [
  { value: 'Month', label: '1M' },
  { value: 'Quarter', label: '3M' },
  { value: 'Year', label: '1Y' },
]

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

  if (!forecastOnly && !(isV2.value && props.realizedHistory.length === 0)) {
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

  if (!historicalOnly && isV2.value && hasBands.value) {
    const bound = (key) =>
      alignSeriesValues(
        props.timeline
          .filter((point) => point[key] !== undefined)
          .map((point) => ({
            date: point.date || point.label,
            label: point.label,
            value: point[key],
          })),
      )
    datasets.push({
      type: 'line',
      label: 'P90 (high cash)',
      data: bound('p90'),
      borderColor: 'transparent',
      backgroundColor: 'transparent',
      pointRadius: 0,
      yAxisID: 'yBalance',
      spanGaps: true,
    })
    datasets.push({
      type: 'line',
      label: 'P10-P90 range',
      data: bound('p10'),
      borderColor: 'transparent',
      backgroundColor: toRgba('#3B82F6', 0.18),
      pointRadius: 0,
      fill: '-1',
      yAxisID: 'yBalance',
      spanGaps: true,
    })
    datasets.push({
      type: 'line',
      label: 'Median (P50)',
      data: bound('p50'),
      borderColor: toRgba('#3B82F6', 0.55),
      backgroundColor: 'transparent',
      pointRadius: 0,
      borderDash: [2, 4],
      yAxisID: 'yBalance',
      spanGaps: true,
    })
  }

  if (!historicalOnly) {
    datasets.push({
      type: 'line',
      label: isV2.value ? 'Liquid cash forecast' : 'Forecast balance',
      data: forecastDataset,
      borderColor: '#3B82F6',
      backgroundColor: toRgba('#3B82F6', 0.15),
      yAxisID: 'yBalance',
      tension: 0.3,
      borderDash: [5, 5],
      spanGaps: true,
    })
  }

  if (!historicalOnly && isV2.value) {
    const palette = ['#F59E0B', '#8B5CF6', '#EF4444', '#14B8A6', '#EC4899']
    props.scenarioLines.forEach((line, index) => {
      datasets.push({
        type: 'line',
        label: line.label,
        data: alignSeriesValues(
          line.timeline.map((point) => ({
            date: point.date,
            label: point.date,
            value: point.liquid_cash,
          })),
        ),
        borderColor: palette[index % palette.length],
        backgroundColor: 'transparent',
        pointRadius: 0,
        borderDash: [8, 3],
        yAxisID: 'yBalance',
        tension: 0.2,
        spanGaps: true,
      })
    })
  }

  return datasets
}

/**
 * Build the active non-balance aspect dataset from backend-typed series payloads.
 */
function buildAspectDatasets() {
  const seriesEntries = [activeSeries.value, ...activeDebtComponentSeries.value].filter(Boolean)
  if (seriesEntries.length === 0) {
    return []
  }

  return seriesEntries
    .map((seriesEntry) => {
      const style = ASPECT_STYLES[seriesEntry.id]
      if (!style) {
        return null
      }

      return {
        type: style.type,
        label: seriesEntry.label,
        data: alignSeriesValues(seriesEntry.points),
        borderColor: style.color,
        backgroundColor: toRgba(style.color, style.type === 'bar' ? 0.45 : 0.15),
        yAxisID: style.axis,
        tension: style.type === 'line' ? 0.25 : 0,
        borderDash: seriesEntry.id === 'debt_totals' ? [4, 4] : [],
        spanGaps: true,
      }
    })
    .filter(Boolean)
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
            text: isV2.value ? 'Liquid cash' : 'Balance',
          },
        },
        yFlow: {
          type: 'linear',
          display: !(isV2.value && props.selectedAspect === 'balances'),
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
          labels: { filter: (item) => item.text !== 'P90 (high cash)' },
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
    props.modelVersion,
    props.scenarioLines,
  ],
  renderChart,
  // 'post' so the <canvas> (rendered behind v-if="hasData") exists when data first arrives.
  { deep: true, flush: 'post' },
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
  flex-wrap: wrap;
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
  font-size: 0.8125rem;
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

<style scoped>
.forecast-range-options { display: flex; flex-wrap: wrap; align-items: center; gap: 0.35rem; }
.forecast-range-options .toggle-button.active { border-color: var(--color-accent-cyan); color: var(--color-accent-cyan); }
</style>
