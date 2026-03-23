<!-- src/components/forecast/ForecastChart.vue -->
<template>
  <div class="chart-container">
    <!-- HEADER -->
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

const ASPECT_META = {
  balances: {
    label: 'Balances',
    subtitle: 'Historical balances are overlaid against projected balances.',
  },
  realized_income: {
    label: 'Realized income',
    subtitle: 'Income points summarize positive non-adjustment cashflows in the forecast range.',
  },
  manual_adjustments: {
    label: 'Manual adjustments',
    subtitle: 'Manual entries isolate user-entered or adjustment-sourced forecast changes.',
  },
  spending: {
    label: 'Spending',
    subtitle: 'Spending points summarize projected outflows as positive magnitudes.',
  },
  debt: {
    label: 'Debt composition',
    subtitle: 'Debt composition compares current assets, liabilities, and net balance snapshots.',
  },
}

const props = defineProps({
  timeline: { type: Array, default: () => [] },
  realizedHistory: { type: Array, default: () => [] },
  viewType: { type: String, default: 'Month' },
  graphMode: { type: String, default: 'combined' },
  selectedAspect: { type: String, default: 'balances' },
  cashflows: { type: Array, default: () => [] },
  assetBalance: { type: Number, default: 0 },
  liabilityBalance: { type: Number, default: 0 },
  netBalance: { type: Number, default: 0 },
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

const historyLabels = computed(() => props.realizedHistory.map((point) => point.label))
const forecastLabels = computed(() => props.timeline.map((point) => point.label))
const labels = computed(() => [...historyLabels.value, ...forecastLabels.value])
const chartMeta = computed(() => ASPECT_META[props.selectedAspect] || ASPECT_META.balances)
const chartTitle = computed(() => `${props.viewType} · ${chartMeta.value.label}`)
const chartSubtitle = computed(() => chartMeta.value.subtitle)
const chartDatasets = computed(() =>
  buildAspectDatasets({
    selectedAspect: props.selectedAspect,
    graphMode: props.graphMode,
    realizedHistory: props.realizedHistory,
    timeline: props.timeline,
    cashflows: props.cashflows,
    assetBalance: props.assetBalance,
    liabilityBalance: props.liabilityBalance,
    netBalance: props.netBalance,
  }),
)
const hasData = computed(
  () =>
    labels.value.length > 0 &&
    chartDatasets.value.some((dataset) => dataset.data.some((value) => value !== null)),
)

/**
 * Emit the opposite timeframe while leaving the active aspect untouched.
 */
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
 * Tear down any prior Chart.js instance before a re-render.
 */
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
      scales: { y: { beginAtZero: false } },
      plugins: {
        legend: {
          display: chartDatasets.value.length > 1,
        },
      },
    },
  })
}

/**
 * Build Chart.js datasets for the active forecast aspect.
 *
 * @param {{
 *   selectedAspect: string,
 *   graphMode: string,
 *   realizedHistory: Array<{ label: string, balance?: number | null }>,
 *   timeline: Array<{ label: string, forecast_balance?: number | null }>,
 *   cashflows: Array<{ date?: string, label?: string, amount?: number | null, source?: string }>,
 *   assetBalance: number,
 *   liabilityBalance: number,
 *   netBalance: number,
 * }} options
 * @returns {Array<{label: string, data: Array<number | null>, borderColor: string, tension: number, borderDash: number[]}>}
 */
function buildAspectDatasets({
  selectedAspect,
  graphMode,
  realizedHistory,
  timeline,
  cashflows,
  assetBalance,
  liabilityBalance,
  netBalance,
}) {
  const historyLength = realizedHistory.length
  const forecastLength = timeline.length
  const historyBalanceData = realizedHistory.map((point) => normalizeNumber(point.balance))
  const forecastBalanceData = timeline.map((point) => normalizeNumber(point.forecast_balance))
  const forecastTimelineLabels = timeline.map((point) => point.label)

  const aspectBuilders = {
    balances: () => [
      makeHistoricalDataset(
        'Historical balance',
        historyBalanceData,
        forecastLength,
        graphMode,
        '#10B981',
      ),
      makeForecastDataset(
        'Projected balance',
        forecastBalanceData,
        historyLength,
        graphMode,
        '#3B82F6',
      ),
    ],
    realized_income: () => [
      makeForecastDataset(
        'Projected income',
        aggregateCashflowsByLabel({
          labels: forecastTimelineLabels,
          cashflows,
          include: (item) => item.amount > 0 && item.source !== 'adjustment',
          transform: (amount) => amount,
        }),
        historyLength,
        '#16A34A',
        { ignoreGraphMode: true },
      ),
    ],
    manual_adjustments: () => [
      makeForecastDataset(
        'Manual adjustments',
        aggregateCashflowsByLabel({
          labels: forecastTimelineLabels,
          cashflows,
          include: (item) => item.source === 'adjustment',
          transform: (amount) => amount,
        }),
        historyLength,
        '#7C3AED',
        { ignoreGraphMode: true },
      ),
    ],
    spending: () => [
      makeForecastDataset(
        'Projected spending',
        aggregateCashflowsByLabel({
          labels: forecastTimelineLabels,
          cashflows,
          include: (item) => item.amount < 0 && item.source !== 'adjustment',
          transform: (amount) => Math.abs(amount),
        }),
        historyLength,
        '#DC2626',
        { ignoreGraphMode: true },
      ),
    ],
    debt: () => {
      const snapshotLength = historyLength + forecastLength
      return [
        makeStaticDataset('Assets', assetBalance, snapshotLength, '#0EA5E9'),
        makeStaticDataset('Liabilities', liabilityBalance, snapshotLength, '#F97316'),
        makeStaticDataset('Net balance', netBalance, snapshotLength, '#111827'),
      ]
    },
  }

  const datasets = (aspectBuilders[selectedAspect] || aspectBuilders.balances)()
  return datasets.filter((dataset) => dataset.data.some((value) => value !== null))
}

/**
 * Keep chart values numeric and convert absent points into nulls.
 *
 * @param {number | null | undefined} value
 * @returns {number | null}
 */
function normalizeNumber(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

/**
 * Prefix a forecast-only dataset with nulls so it aligns after realized history.
 *
 * @param {string} label
 * @param {Array<number | null>} values
 * @param {number} historyLength
 * @param {string} graphMode
 * @param {string} borderColor
 * @param {{ ignoreGraphMode?: boolean }} [options]
 */
function makeForecastDataset(label, values, historyLength, graphMode, borderColor, options = {}) {
  const isHidden = !options.ignoreGraphMode && graphMode === 'historical'
  return {
    label,
    data: isHidden ? [] : [...new Array(historyLength).fill(null), ...values],
    borderColor,
    tension: 0.3,
    borderDash: [5, 5],
  }
}

/**
 * Pad a realized-history dataset so it stops before forecast points begin.
 *
 * @param {string} label
 * @param {Array<number | null>} values
 * @param {number} forecastLength
 * @param {string} graphMode
 * @param {string} borderColor
 */
function makeHistoricalDataset(label, values, forecastLength, graphMode, borderColor) {
  const isHidden = graphMode === 'forecast'
  return {
    label,
    data: isHidden ? [] : [...values, ...new Array(forecastLength).fill(null)],
    borderColor,
    tension: 0.3,
    borderDash: [],
  }
}

/**
 * Create a constant-value dataset for snapshot-style comparisons.
 *
 * @param {string} label
 * @param {number} value
 * @param {number} pointCount
 * @param {string} borderColor
 */
function makeStaticDataset(label, value, pointCount, borderColor) {
  return {
    label,
    data: new Array(pointCount).fill(normalizeNumber(value)),
    borderColor,
    tension: 0.15,
    borderDash: [],
  }
}

/**
 * Aggregate forecast cashflows onto the displayed timeline labels.
 *
 * @param {{
 *   labels: string[],
 *   cashflows: Array<{ date?: string, label?: string, amount?: number | null }>,
 *   include: (item: { amount?: number | null, source?: string }) => boolean,
 *   transform: (amount: number) => number,
 * }} options
 * @returns {Array<number | null>}
 */
function aggregateCashflowsByLabel({ labels, cashflows, include, transform }) {
  const totals = new Map()

  // The API can emit multiple cashflow rows per day, so the chart collapses them into a single
  // point per rendered label before plotting the selected aspect.
  cashflows.forEach((item) => {
    if (!include(item)) {
      return
    }

    const key = String(item.date || item.label || '')
    if (!key) {
      return
    }

    totals.set(key, (totals.get(key) ?? 0) + transform(Number(item.amount ?? 0)))
  })

  return labels.map((label) => normalizeNumber(totals.get(label) ?? null))
}

onMounted(renderChart)
onBeforeUnmount(destroyChart)
watch(
  () => [
    props.timeline,
    props.realizedHistory,
    props.graphMode,
    props.selectedAspect,
    props.cashflows,
    props.assetBalance,
    props.liabilityBalance,
    props.netBalance,
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
  gap: 1rem;
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
