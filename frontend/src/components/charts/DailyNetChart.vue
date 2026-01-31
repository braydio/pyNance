<template>
  <div class="daily-net-chart">
    <div style="height: 400px">
      <canvas ref="chartCanvas" style="width: 100%; height: 100%"></canvas>
    </div>
  </div>
</template>

<script setup>
/**
 * DailyNetChart.vue
 *
 * Renders the dashboard daily net chart with stacked income/expense bars,
 * a net indicator dash, and a detail tooltip aligned to the net value.
 */
import { fetchDailyNet } from '@/api/charts'
import { ref, onMounted, onUnmounted, nextTick, watch, toRefs } from 'vue'
import { Chart } from 'chart.js'
import { formatAmount } from '@/utils/format'

// Register Chart.js plugins globally
import {
  Tooltip,
  Legend,
  LineElement,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
} from 'chart.js'

Chart.register(Tooltip, Legend, LineElement, BarElement, CategoryScale, LinearScale, PointElement)

/**
 * Resolve the pixel position for the net indicator at a given label index.
 *
 * @param {import('chart.js').Chart} chart - The chart instance.
 * @param {number} dataIndex - Active label index.
 * @returns {{x: number, y: number} | null} Pixel coordinates for the net dash.
 */
function getNetDashPosition(chart, dataIndex) {
  if (!chart?.getDatasetMeta) return null
  const firstMeta = chart.getDatasetMeta(0)
  const bar = firstMeta?.data?.[dataIndex]
  const netValues = chart.$netValues
  const netRows = chart.$dailyNetRows
  const yScale = chart.scales?.y
  const netValue =
    netValues?.[dataIndex] ?? netRows?.[dataIndex]?.net?.parsedValue ?? netRows?.[dataIndex]?.net
  if (!bar || netValue == null || !yScale) return null
  return { x: bar.x, y: yScale.getPixelForValue(netValue) }
}

/**
 * Resolve the pixel position for the zero line at a given label index.
 *
 * @param {import('chart.js').Chart} chart - The chart instance.
 * @param {number} dataIndex - Active label index.
 * @returns {{x: number, y: number} | null} Pixel coordinates for y=0.
 */
function getZeroLinePosition(chart, dataIndex) {
  if (!chart?.getDatasetMeta) return null
  const firstMeta = chart.getDatasetMeta(0)
  const bar = firstMeta?.data?.[dataIndex]
  const yScale = chart.scales?.y
  if (!bar || !yScale) return null
  return { x: bar.x, y: yScale.getPixelForValue(0) }
}

function registerTooltipPositioner(name, positioner) {
  const targets = [Tooltip?.positioners, Chart?.Tooltip?.positioners]
  targets.forEach((target) => {
    if (target && !target[name]) target[name] = positioner
  })
}

// --- Safe registration for custom tooltip positioner ---
registerTooltipPositioner('zeroLine', function (items, eventPosition) {
  /**
   * Anchor tooltips to the zero line instead of the hover cursor.
   *
   * @param {Array} items - Tooltip items for the active index.
   * @param {{x: number, y: number}} eventPosition - Fallback cursor position.
   * @returns {{x: number, y: number}} Tooltip anchor coordinates.
   */
  if (!items?.length) return eventPosition
  const chart = items[0]?.chart
  const dataIndex = items[0].dataIndex
  const position = getZeroLinePosition(chart, dataIndex)
  return position ?? eventPosition
})
// ----------------------------------------------------------------------

/**
 * Render the daily net stacked bar chart with income, expenses, and net overlays.
 * Includes optional moving averages and comparison overlays to contextualize trends.
 */

// Props
const props = defineProps({
  startDate: { type: String, required: true },
  endDate: { type: String, required: true },
  zoomedOut: { type: Boolean, default: false },
  show7Day: { type: Boolean, default: false },
  show30Day: { type: Boolean, default: false },
  showAvgIncome: { type: Boolean, default: false },
  showAvgExpenses: { type: Boolean, default: false },
  showComparisonOverlay: { type: Boolean, default: false },
  timeframe: {
    type: String,
    default: 'mtd',
    validator: (value) => ['mtd', 'rolling_30'].includes(value),
  },
})

const { show7Day, show30Day, showAvgIncome, showAvgExpenses, showComparisonOverlay, timeframe } =
  toRefs(props)

const emit = defineEmits(['bar-click', 'summary-change', 'data-change'])

const chartInstance = ref(null)
const chartCanvas = ref(null)
const chartData = ref([])
const comparisonData = ref([])
const requestRange = ref({ startDate: null, endDate: null, displayStart: null, displayEnd: null })

const MS_PER_DAY = 86400000
const DEFAULT_ZOOM_MONTHS = 6

const getStyle = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()

/**
 * Return the normalized tooltip data for a given chart index.
 *
 * @param {import('chart.js').Chart} chart - The chart instance.
 * @param {number} dataIndex - The active data index.
 * @returns {Object|null} Tooltip payload with row data and comparison info.
 */
function getTooltipPayload(chart, dataIndex) {
  const row = chart?.$dailyNetRows?.[dataIndex]
  if (!row) return null
  return {
    row,
    comparisonLabel: chart?.$comparisonLabel || '',
    comparisonValue: chart?.$comparisonSeries?.[dataIndex] ?? null,
  }
}

/**
 * Build the tooltip body lines for the daily net chart.
 *
 * @param {Object} payload - Tooltip payload.
 * @param {Object} payload.row - Daily net row data.
 * @param {string} payload.comparisonLabel - Label for the comparison series.
 * @param {number|null} payload.comparisonValue - Comparison series value.
 * @returns {string[]} Tooltip lines to render.
 */
function buildTooltipLines({ row, comparisonLabel, comparisonValue }) {
  const lines = [
    `Income: ${formatAmount(row.income.parsedValue)}`,
    `Expenses: ${formatAmount(row.expenses.parsedValue)}`,
    `Net: ${formatAmount(row.net.parsedValue)}`,
    `Transactions: ${row.transaction_count ?? 0}`,
  ]

  if (comparisonLabel && comparisonValue != null) {
    lines.push('', `${comparisonLabel}: ${formatAmount(comparisonValue)}`)
  }

  return lines
}

function formatDateKey(date) {
  const d = date instanceof Date && !Number.isNaN(date) ? date : new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`
}

function parseDateKey(str) {
  if (!str) return null
  const d = new Date(`${str}T00:00:00`)
  return Number.isNaN(d) ? null : d
}

const formatTooltipTitle = (label) => {
  const parsed = parseDateKey(label)
  return parsed
    ? parsed.toLocaleDateString(undefined, { month: 'short', day: '2-digit', year: 'numeric' })
    : label
}

function formatAxisLabel(label) {
  const parsed = parseDateKey(label)
  return parsed ? parsed.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : label
}

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

function createEmptyDailyNetEntry(date) {
  return {
    date,
    income: { parsedValue: 0 },
    expenses: { parsedValue: 0 },
    net: { parsedValue: 0 },
    transaction_count: 0,
  }
}

function padDailyNetData(data, labels) {
  const map = new Map((data || []).map((d) => [d.date, d]))
  return labels.map((l) => map.get(l) ?? createEmptyDailyNetEntry(l))
}

function movingAverage(values, window) {
  return values.map((_, i) =>
    i < window - 1 ? null : values.slice(i - window + 1, i + 1).reduce((a, b) => a + b, 0) / window,
  )
}

function buildLineDataset(label, data, color, overrides = {}) {
  return {
    type: 'line',
    label,
    data,
    borderColor: color,
    backgroundColor: 'transparent',
    borderWidth: 2,
    tension: 0.25,
    pointRadius: 0,
    spanGaps: true,
    fill: false,
    ...overrides,
  }
}

function emphasizeColor(hex, channel = 'g') {
  return hex
}

function getZoomedDisplayRange() {
  const end = parseDateKey(props.endDate) ?? new Date()
  const start = parseDateKey(props.startDate) ?? new Date(end)
  if (!props.startDate) start.setMonth(start.getMonth() - DEFAULT_ZOOM_MONTHS)
  return { startDate: formatDateKey(start), endDate: formatDateKey(end) }
}

function getActiveLabelRange() {
  if (!props.zoomedOut) return { startDate: props.startDate, endDate: props.endDate }

  const zoomed = getZoomedDisplayRange()
  return {
    startDate: props.startDate || requestRange.value.displayStart || zoomed.startDate,
    endDate: props.endDate || requestRange.value.displayEnd || zoomed.endDate,
  }
}

function getDisplaySeries() {
  const { startDate, endDate } = getActiveLabelRange()
  const labels = buildDateRangeLabels(startDate, endDate)
  return { labels, displayData: padDailyNetData(chartData.value, labels) }
}

function getExtendedSeries() {
  const displayRange = getActiveLabelRange()
  const startDate = requestRange.value.startDate || displayRange.startDate
  const endDate = requestRange.value.endDate || displayRange.endDate
  const labels = buildDateRangeLabels(startDate, endDate)
  return { labels, fullData: padDailyNetData(chartData.value, labels) }
}

function mapSeriesToDisplay(labels, fullLabels, fullSeries) {
  const labelIndex = new Map(fullLabels.map((label, index) => [label, index]))
  return labels.map((label) => {
    const idx = labelIndex.get(label)
    return idx == null ? null : (fullSeries[idx] ?? null)
  })
}

function buildComparisonContext() {
  const end = parseDateKey(props.endDate)
  const start = parseDateKey(props.startDate)
  if (!end || !start) return null

  if (timeframe.value === 'mtd') {
    const priorMonthStart = new Date(end.getFullYear(), end.getMonth() - 1, 1)
    const last = new Date(end.getFullYear(), end.getMonth(), 0)
    const day = Math.min(end.getDate(), last.getDate())
    return {
      mode: 'prior_month_to_date',
      priorStart: priorMonthStart,
      priorEnd: new Date(priorMonthStart.getFullYear(), priorMonthStart.getMonth(), day),
    }
  }

  const currentStart = start
  const currentEnd = end
  const priorEnd = new Date(currentStart)
  priorEnd.setDate(priorEnd.getDate() - 1)

  const priorStart = new Date(priorEnd)
  priorStart.setDate(priorStart.getDate() - 29)

  return { mode: 'rolling_30', priorStart, priorEnd, currentStart, currentEnd }
}

function buildComparisonSeries(labels, data, ctx) {
  if (!ctx) return []
  if (ctx.mode === 'prior_month_to_date') {
    const byDay = new Map()
    data.forEach((d) => {
      const parsed = parseDateKey(d.date)
      if (parsed) byDay.set(parsed.getDate(), d.net.parsedValue)
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

// Chart plugin
const netDashPlugin = {
  id: 'netDashPlugin',
  /**
   * Draw the yellow net indicator dash for each bar.
   *
   * @param {import('chart.js').Chart} chart - Chart instance.
   * @returns {void}
   */
  afterDatasetsDraw(chart) {
    if (!chart?.ctx || !chart?.getDatasetMeta) return
    const firstMeta = chart.getDatasetMeta(0)

    if (!firstMeta?.data?.length) return

    firstMeta.data.forEach((_, index) => {
      const position = getNetDashPosition(chart, index)
      if (!position) return
      const { x, y } = position
      const { ctx } = chart
      if (!ctx?.save) return
      ctx.save()
      ctx.strokeStyle = getStyle('--color-accent-yellow')
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(x - 10, y)
      ctx.lineTo(x + 10, y)
      ctx.stroke()
      ctx.restore()
    })
  },
}

const tooltipSnapPlugin = {
  id: 'tooltipSnapPlugin',
  /**
   * Force the tooltip caret to align with the zero line.
   *
   * @param {import('chart.js').Chart} chart - Chart instance.
   * @param {{ tooltip?: { dataPoints?: Array<{ dataIndex: number }>, caretX?: number, caretY?: number, x?: number, y?: number } }} args - Tooltip draw args.
   * @returns {void}
   */
  beforeTooltipDraw(chart, args) {
    const tooltip = args?.tooltip
    const dataIndex = tooltip?.dataPoints?.[0]?.dataIndex
    if (dataIndex == null) return
    const position = getZeroLinePosition(chart, dataIndex)
    if (!position) return
    tooltip.caretX = position.x
    tooltip.caretY = position.y
    tooltip.x = position.x
    tooltip.y = position.y
  },
}

function handleBarClick(evt) {
  if (!chartInstance.value) return
  const points = chartInstance.value.getElementsAtEventForMode(
    evt,
    'nearest',
    { intersect: true },
    false,
  )
  if (points.length) emit('bar-click', chartInstance.value.data.labels[points[0].index])
}

/**
 * Render the Daily Net chart and cache tooltip metadata for hover callbacks.
 *
 * @returns {Promise<void>} Resolves after the chart is rendered.
 */
async function renderChart() {
  await nextTick()
  if (chartInstance.value) {
    chartInstance.value.stop()
    chartInstance.value.destroy()
  }

  const ctx = chartCanvas.value?.getContext('2d')
  if (!ctx) return

  const { labels, displayData } = getDisplaySeries()
  const { labels: fullLabels, fullData } = getExtendedSeries()
  if (!labels.length) return

  emit(
    'summary-change',
    displayData.reduce(
      (a, r) => ({
        totalIncome: a.totalIncome + r.income.parsedValue,
        totalExpenses: a.totalExpenses + r.expenses.parsedValue,
        totalNet: a.totalNet + r.net.parsedValue,
      }),
      { totalIncome: 0, totalExpenses: 0, totalNet: 0 },
    ),
  )
  emit('data-change', displayData)

  const income = displayData.map((d) => d.income.parsedValue)
  const expenses = displayData.map((d) => d.expenses.parsedValue)
  const net = displayData.map((d) => d.net.parsedValue)
  const fullNet = fullData.map((d) => d.net.parsedValue)
  const fullIncome = fullData.map((d) => d.income.parsedValue)
  const fullExpenses = fullData.map((d) => d.expenses.parsedValue)
  const full7Day = movingAverage(fullNet, 7)
  const full30Day = movingAverage(fullNet, 30)
  const display7Day = mapSeriesToDisplay(labels, fullLabels, full7Day)
  const display30Day = mapSeriesToDisplay(labels, fullLabels, full30Day)
  const averageIncome = fullIncome.length
    ? fullIncome.reduce((a, b) => a + b, 0) / fullIncome.length
    : 0
  const averageExpenses = fullExpenses.length
    ? fullExpenses.reduce((a, b) => a + b, 0) / fullExpenses.length
    : 0

  const incomeColor = getStyle('--color-accent-green') || '#22c55e'
  const expenseColor = getStyle('--color-accent-red') || '#ef4444'
  const averageIncomeColor = emphasizeColor(incomeColor, 'g')
  const averageExpensesColor = emphasizeColor(expenseColor, 'r')
  const comparisonColor = getStyle('--color-accent-blue') || '#719cd6'
  const sevenDayColor = getStyle('--color-accent-cyan') || '#63cdcf'
  const thirtyDayColor = getStyle('--color-accent-purple') || '#9d79d6'
  const fontFamily = getStyle('--font-chart') || 'ui-sans-serif, system-ui, sans-serif'

  const stackId = 'daily-stack'
  const datasets = [
    {
      type: 'bar',
      label: 'Expenses',
      data: expenses,
      barThickness: 18,
      backgroundColor: expenseColor,
      borderColor: expenseColor,
      borderWidth: 1,
      stack: stackId,
      order: 1,
    },
    {
      type: 'bar',
      label: 'Income',
      data: income,
      barThickness: 18,
      backgroundColor: incomeColor,
      borderColor: incomeColor,
      borderWidth: 1,
      stack: stackId,
      order: 2,
    },
  ]

  if (showAvgIncome.value)
    datasets.push(
      buildLineDataset(
        'Avg Income',
        labels.map(() => averageIncome),
        averageIncomeColor,
        { borderDash: [6, 6], order: 4 },
      ),
    )

  if (showAvgExpenses.value)
    datasets.push(
      buildLineDataset(
        'Avg Expenses',
        labels.map(() => averageExpenses),
        averageExpensesColor,
        { borderDash: [4, 8], order: 5 },
      ),
    )

  let comparisonSeries = null
  let comparisonLabel = ''

  if (showComparisonOverlay.value) {
    const ctx = buildComparisonContext()
    comparisonSeries = buildComparisonSeries(labels, comparisonData.value, ctx)
    comparisonLabel =
      ctx?.mode === 'prior_month_to_date' ? 'This Day Last Month' : 'This Day Last Month'
    datasets.push(
      buildLineDataset(comparisonLabel, comparisonSeries, comparisonColor, {
        borderDash: [2, 6],
        order: 6,
      }),
    )
  }

  if (show30Day.value)
    datasets.push(
      buildLineDataset('30-Day Avg', display30Day, thirtyDayColor, {
        borderDash: [8, 4],
        borderWidth: 3,
        order: 7,
      }),
    )

  if (show7Day.value)
    datasets.push(
      buildLineDataset('7-Day Avg', display7Day, sevenDayColor, {
        borderDash: [2, 2],
        borderWidth: 3,
        order: 8,
      }),
    )

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    plugins: [netDashPlugin, tooltipSnapPlugin],
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      onClick: handleBarClick,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            autoSkip: true,
            maxTicksLimit: 8,
            color: getStyle('--color-text-muted'),
            font: { family: fontFamily, size: 12 },
            callback: (_, index) => formatAxisLabel(labels[index]),
          },
        },
        y: {
          stacked: true,
          grid: { color: getStyle('--divider') || 'rgba(255,255,255,0.08)' },
          ticks: {
            color: getStyle('--color-text-muted'),
            font: { family: fontFamily, size: 12 },
            callback: (value) => formatAmount(value),
          },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: getStyle('--theme-bg'),
          borderColor: getStyle('--color-accent-yellow'),
          borderWidth: 1,
          padding: 12,
          displayColors: false,
          mode: 'index',
          intersect: false,
          titleColor: getStyle('--color-accent-yellow'),
          bodyColor: getStyle('--color-text-light'),
          titleFont: { family: "'Fira Code', monospace", weight: '600' },
          bodyFont: { family: "'Fira Code', monospace" },
          cornerRadius: 10,
          caretPadding: 6,
          caretSize: 9,
          bodySpacing: 6,
          titleSpacing: 4,
          titleMarginBottom: 6,
          position: 'zeroLine',
          callbacks: {
            title: (items) => formatTooltipTitle(items[0]?.label ?? ''),
            label: (context) => {
              if (context.datasetIndex !== 0) return null
              const payload = getTooltipPayload(context.chart, context.dataIndex)
              return payload ? buildTooltipLines(payload) : null
            },
          },
        },
      },
    },
  })
  // Cache tooltip-specific metadata on the chart instance for fast lookup.
  chartInstance.value.$dailyNetRows = displayData
  chartInstance.value.$comparisonSeries = comparisonSeries
  chartInstance.value.$comparisonLabel = comparisonLabel
  chartInstance.value.$netValues = net
}

async function fetchData() {
  const display = props.zoomedOut ? getZoomedDisplayRange() : props
  const start = parseDateKey(display.startDate) ?? new Date()
  start.setDate(start.getDate() - 30)

  requestRange.value = {
    startDate: formatDateKey(start),
    endDate: display.endDate,
    displayStart: display.startDate,
    displayEnd: display.endDate,
  }

  const res = await fetchDailyNet({
    start_date: requestRange.value.startDate,
    end_date: requestRange.value.endDate,
  })

  if (res.status === 'success') chartData.value = res.data
}

async function fetchComparisonData() {
  if (!showComparisonOverlay.value) return (comparisonData.value = [])
  const ctx = buildComparisonContext()
  if (!ctx) return (comparisonData.value = [])

  const res = await fetchDailyNet({
    start_date: formatDateKey(ctx.priorStart),
    end_date: formatDateKey(ctx.priorEnd),
  })

  if (res.status === 'success') comparisonData.value = res.data
}

watch([chartData, comparisonData, show7Day, show30Day, showAvgIncome, showAvgExpenses], renderChart)
watch(() => [props.startDate, props.endDate, props.zoomedOut], fetchData)
watch(
  () => [timeframe.value, showComparisonOverlay.value, props.startDate, props.endDate],
  fetchComparisonData,
)

onMounted(() => {
  fetchData()
  fetchComparisonData()
})
onUnmounted(() => chartInstance.value?.destroy())
</script>
