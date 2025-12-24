<template>
  <div class="daily-net-chart">
    <div style="height: 400px">
      <canvas ref="chartCanvas" style="width: 100%; height: 100%"></canvas>
    </div>
  </div>
</template>

<script setup>
/**
 * Displays income, expenses, and net totals for the selected date range.
 *
 * - Fully padded date ranges (no missing days)
 * - Moving averages calculated from extended fetch window
 * - Comparison overlays correctly aligned
 * - No duplicate consts / merge artifacts
 */
import { fetchDailyNet } from '@/api/charts'
import { ref, onMounted, onUnmounted, nextTick, watch, toRefs } from 'vue'
import { Chart } from 'chart.js/auto'
import { formatAmount } from '@/utils/format'

const props = defineProps({
  startDate: { type: String, required: true },
  endDate: { type: String, required: true },
  zoomedOut: { type: Boolean, default: false },
  show7Day: { type: Boolean, default: false },
  show30Day: { type: Boolean, default: false },
  showAvgIncome: { type: Boolean, default: false },
  showAvgExpenses: { type: Boolean, default: false },
  showComparisonOverlay: { type: Boolean, default: false },
  comparisonMode: { type: String, default: 'prior_month_to_date' },
})

const {
  show7Day,
  show30Day,
  showAvgIncome,
  showAvgExpenses,
  showComparisonOverlay,
  comparisonMode,
} = toRefs(props)

const emit = defineEmits(['bar-click', 'summary-change', 'data-change'])

const chartInstance = ref(null)
const chartCanvas = ref(null)
const chartData = ref([])
const comparisonData = ref([])
const requestRange = ref({ startDate: null, endDate: null, displayStart: null, displayEnd: null })

const MS_PER_DAY = 24 * 60 * 60 * 1000
const DEFAULT_ZOOM_MONTHS = 6

const getStyle = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()

/**
 * Format a Date object as YYYY-MM-DD without timezone shifts.
 *
 * @param {Date} date - Date to format.
 * @returns {string} ISO-like date string.
 */
function formatDateKey(date) {
  const safeDate = date instanceof Date && !Number.isNaN(date.getTime()) ? date : new Date()
  return `${safeDate.getFullYear()}-${String(safeDate.getMonth() + 1).padStart(2, '0')}-${String(
    safeDate.getDate(),
  ).padStart(2, '0')}`
}

/**
 * Parse a YYYY-MM-DD date string into a Date object at local midnight.
 *
 * @param {string} dateString - Date string to parse.
 * @returns {Date|null} Parsed date or null if invalid.
 */
function parseDateKey(dateString) {
  if (!dateString) return null
  const parsed = new Date(`${dateString}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return null
  return parsed
}

/**
 * Build a contiguous list of labels between the provided start and end dates.
 *
 * @param {string} startDate - Inclusive start date.
 * @param {string} endDate - Inclusive end date.
 * @returns {string[]} Array of daily labels.
 */
function buildDateRangeLabels(startDate, endDate) {
  const start = parseDateKey(startDate)
  const end = parseDateKey(endDate)
  if (!start || !end) return []

  const labels = []
  const cur = new Date(Math.min(start, end))
  const last = new Date(Math.max(start, end))

  while (cur <= last) {
    labels.push(formatDateKey(cur))
    cur.setDate(cur.getDate() + 1)
  }

  return labels
}

/**
 * Normalize an empty daily net entry.
 *
 * @param {string} date - Date label for the placeholder entry.
 * @returns {object} Placeholder record with zero values.
 */
function createEmptyDailyNetEntry(date) {
  return {
    date,
    income: { parsedValue: 0 },
    expenses: { parsedValue: 0 },
    net: { parsedValue: 0 },
    transaction_count: 0,
  }
}

/**
 * Pad missing dates with zero-value entries so arrays stay aligned to labels.
 *
 * @param {Array} data - Raw API data for the range.
 * @param {string[]} labels - Contiguous date labels.
 * @returns {Array} Padded entries aligned to labels.
 */
function padDailyNetData(data, labels) {
  const map = new Map((data || []).map((d) => [d.date, d]))
  return labels.map((l) => map.get(l) ?? createEmptyDailyNetEntry(l))
}

/**
 * Compute a simple moving average over the provided values.
 *
 * @param {number[]} values - Series of numeric values.
 * @param {number} window - Window size for the average.
 * @returns {(number | null)[]} Moving-average values aligned to the source indices.
 */
function movingAverage(values, window) {
  return values.map((_, i) =>
    i < window - 1 ? null : values.slice(i - window + 1, i + 1).reduce((a, b) => a + b, 0) / window,
  )
}

/**
 * Determine the display window when zoomed out, favoring supplied props or
 * defaulting to the last DEFAULT_ZOOM_MONTHS months.
 *
 * @returns {{ startDate: string, endDate: string }} Start/end boundaries for zoomed display.
 */
function getZoomedDisplayRange() {
  const end = parseDateKey(props.endDate) ?? new Date()
  const start = parseDateKey(props.startDate) ?? new Date(end)
  if (!props.startDate) start.setMonth(start.getMonth() - DEFAULT_ZOOM_MONTHS)
  return { startDate: formatDateKey(start), endDate: formatDateKey(end) }
}

/**
 * Build the active label range for rendering, using display boundaries rather
 * than the extended fetch window.
 *
 * @returns {{ startDate: string|null, endDate: string|null }} Label boundaries for the chart.
 */
function getActiveLabelRange() {
  if (!props.zoomedOut) return { startDate: props.startDate, endDate: props.endDate }

  const zoomed = getZoomedDisplayRange()
  return {
    startDate: props.startDate || requestRange.value.displayStart || zoomed.startDate,
    endDate: props.endDate || requestRange.value.displayEnd || zoomed.endDate,
  }
}

/**
 * Produce labels and padded data aligned to the active range.
 *
 * @returns {{ labels: string[], displayData: Array }} Contiguous labels and matching entries.
 */
function getDisplaySeries() {
  const { startDate, endDate } = getActiveLabelRange()
  const labels = buildDateRangeLabels(startDate, endDate)
  return { labels, displayData: padDailyNetData(chartData.value, labels) }
}

function buildComparisonContext() {
  const end = parseDateKey(props.endDate)
  if (!end) return null

  if (comparisonMode.value === 'prior_month_to_date') {
    const start = new Date(end.getFullYear(), end.getMonth() - 1, 1)
    const last = new Date(end.getFullYear(), end.getMonth(), 0)
    const day = Math.min(end.getDate(), last.getDate())
    return {
      mode: 'prior_month_to_date',
      priorStart: start,
      priorEnd: new Date(start.getFullYear(), start.getMonth(), day),
    }
  }

  const currentEnd = end
  const currentStart = new Date(currentEnd)
  currentStart.setDate(currentEnd.getDate() - 29)

  const priorEnd = new Date(currentStart)
  priorEnd.setDate(priorEnd.getDate() - 1)

  const priorStart = new Date(priorEnd)
  priorStart.setDate(priorStart.getDate() - 29)

  return { mode: 'last_30_vs_previous_30', priorStart, priorEnd, currentStart, currentEnd }
}

/**
 * Align comparison data to the current label set.
 *
 * @param {string[]} labels - Active chart labels.
 * @param {Array} data - Comparison series data.
 * @param {object|null} ctx - Comparison context metadata.
 * @returns {(number|null)[]} Net values aligned to labels.
 */
function buildComparisonSeries(labels, data, ctx) {
  if (!ctx) return []

  if (ctx.mode === 'prior_month_to_date') {
    const byDay = new Map()
    data.forEach((d) => {
      const parsed = parseDateKey(d.date)
      if (!parsed) return
      byDay.set(parsed.getDate(), d.net.parsedValue)
    })
    return labels.map((l) => {
      const parsed = parseDateKey(l)
      return parsed ? (byDay.get(parsed.getDate()) ?? null) : null
    })
  }

  const byIndex = new Map()
  data.forEach((d) => {
    const parsed = parseDateKey(d.date)
    if (!parsed) return
    const idx = Math.floor((parsed - ctx.priorStart) / MS_PER_DAY)
    if (idx >= 0 && idx < 30) byIndex.set(idx, d.net.parsedValue)
  })

  return labels.map((l) => {
    const parsed = parseDateKey(l)
    if (!parsed) return null
    const idx = Math.floor((parsed - ctx.currentStart) / MS_PER_DAY)
    return byIndex.get(idx) ?? null
  })
}

function emphasizeColor(hex, channel) {
  let n = hex.replace('#', '')
  if (n.length === 3)
    n = n
      .split('')
      .map((c) => c + c)
      .join('')
  let r = parseInt(n.slice(0, 2), 16)
  let g = parseInt(n.slice(2, 4), 16)
  let b = parseInt(n.slice(4, 6), 16)
  const d = 20
  if (channel === 'g') g = Math.min(255, g + d)
  if (channel === 'r') r = Math.min(255, r + d)
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
}

/**
 * Render the chart with padded labels and aligned moving averages.
 */
async function renderChart() {
  await nextTick()
  if (chartInstance.value) chartInstance.value.destroy()

  const ctx = chartCanvas.value?.getContext('2d')
  if (!ctx) return

  const { labels, displayData } = getDisplaySeries()
  if (!labels.length) return

  const net = displayData.map((d) => d.net.parsedValue)
  const income = displayData.map((d) => d.income.parsedValue)
  const expenses = displayData.map((d) => d.expenses.parsedValue)

  const fullLabels = buildDateRangeLabels(
    requestRange.value.startDate || labels[0],
    requestRange.value.endDate || labels.at(-1),
  )
  const paddedFullData = padDailyNetData(chartData.value, fullLabels)
  const allNetValues = paddedFullData.map((d) => d.net.parsedValue)

  const ma7Full = movingAverage(allNetValues, 7)
  const ma30Full = movingAverage(allNetValues, 30)

  const indexByDate = Object.fromEntries(fullLabels.map((l, i) => [l, i]))
  const ma7 = labels.map((l) => ma7Full[indexByDate[l]] ?? null)
  const ma30 = labels.map((l) => ma30Full[indexByDate[l]] ?? null)

  const avgIncome = income.length ? income.reduce((a, b) => a + b, 0) / income.length : 0
  const avgExpenses = expenses.length ? expenses.reduce((a, b) => a + b, 0) / expenses.length : 0

  const comparisonCtx = showComparisonOverlay.value ? buildComparisonContext() : null
  const comparisonSeries = showComparisonOverlay.value
    ? buildComparisonSeries(labels, comparisonData.value, comparisonCtx)
    : []

  const incomeBase = getStyle('--color-accent-green')
  const expenseBase = getStyle('--color-accent-red')

  const datasets = [
    {
      type: 'bar',
      label: 'Income',
      data: income,
      backgroundColor: income.map((v) =>
        v > avgIncome ? emphasizeColor(incomeBase, 'g') : incomeBase,
      ),
      barThickness: 20,
    },
    {
      type: 'bar',
      label: 'Expenses',
      data: expenses,
      backgroundColor: expenseBase,
      barThickness: 20,
    },
    {
      type: 'bar',
      label: 'Net',
      data: net,
      backgroundColor: 'transparent',
      barThickness: 20,
    },
    { type: 'line', label: '7-Day Avg', data: ma7, borderWidth: 2, pointRadius: 0 },
    { type: 'line', label: '30-Day Avg', data: ma30, borderWidth: 2, pointRadius: 0 },
  ]

  if (comparisonCtx) {
    datasets.push({
      type: 'line',
      label: 'Prior month to-date',
      data: comparisonSeries,
      borderColor: getStyle('--color-accent-purple'),
      borderDash: [6, 4],
      borderWidth: 2,
      pointRadius: 0,
    })
  }

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { ticks: { callback: (v) => formatAmount(v) } },
      },
    },
  })
}

/**
 * Fetch chart data for the active window while extending the request to pad moving averages.
 */
async function fetchData() {
  const displayRange = props.zoomedOut
    ? getZoomedDisplayRange()
    : { startDate: props.startDate, endDate: props.endDate }

  const start = parseDateKey(displayRange.startDate) ?? new Date()
  start.setDate(start.getDate() - 30)

  const params = {
    start_date: formatDateKey(start),
    end_date: displayRange.endDate,
  }

  requestRange.value = {
    startDate: params.start_date,
    endDate: params.end_date,
    displayStart: displayRange.startDate,
    displayEnd: displayRange.endDate,
  }
  const res = await fetchDailyNet(params)
  if (res.status === 'success') chartData.value = res.data
}

/**
 * Fetch comparison overlay data when enabled.
 */
async function fetchComparisonData() {
  if (!showComparisonOverlay.value) {
    comparisonData.value = []
    return
  }

  const ctx = buildComparisonContext()
  if (!ctx) {
    comparisonData.value = []
    return
  }

  const params = {
    start_date: formatDateKey(ctx.priorStart),
    end_date: formatDateKey(ctx.priorEnd),
  }
  const res = await fetchDailyNet(params)
  if (res.status === 'success') comparisonData.value = res.data
}

watch([chartData, show7Day, show30Day, showAvgIncome, showAvgExpenses, comparisonData], renderChart)
watch(() => [props.startDate, props.endDate, props.zoomedOut], fetchData)
watch(
  () => [
    props.startDate,
    props.endDate,
    props.zoomedOut,
    comparisonMode.value,
    showComparisonOverlay.value,
  ],
  fetchComparisonData,
)

onMounted(() => {
  fetchData()
  fetchComparisonData()
})
onUnmounted(() => chartInstance.value?.destroy())
</script>
