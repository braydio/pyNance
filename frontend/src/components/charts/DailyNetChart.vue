<template>
  <div class="daily-net-chart">
    <div style="height: 400px">
      <canvas ref="chartCanvas" style="width: 100%; height: 100%"></canvas>
    </div>
  </div>
</template>

<script setup>
import { fetchDailyNet } from '@/api/charts'
import { ref, onMounted, onUnmounted, nextTick, watch, toRefs } from 'vue'
import { Chart } from 'chart.js/auto'
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

// --- Safe registration for custom tooltip positioner ---
if (Chart?.Tooltip?.positioners && !Chart.Tooltip.positioners.netDash) {
  Chart.Tooltip.positioners.netDash = function (items, eventPosition) {
    if (!items?.length) return eventPosition
    const chart = items[0].chart
    const netIdx = chart.data.datasets.findIndex((d) => d.netIndicator)
    const dataIndex = items[0].dataIndex
    if (netIdx === -1) return eventPosition
    const meta = chart.getDatasetMeta(netIdx)
    const point = meta?.data?.[dataIndex]
    const fallbackPoint = items[0].element
    if (point) return { x: point.x, y: point.y - 8 }
    if (fallbackPoint) return { x: fallbackPoint.x, y: fallbackPoint.y - 8 }
    return eventPosition ?? { x: 0, y: 0 }
  }
}
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
      return parsed ? byDay.get(parsed.getDate()) ?? null : null
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
const netLinePlugin = {
  id: 'netLinePlugin',
  afterDatasetsDraw(chart) {
    const idx = chart.data.datasets.findIndex((d) => d.netIndicator)
    if (idx === -1) return
    const meta = chart.getDatasetMeta(idx)
    meta.data.forEach((bar) => {
      const { ctx } = chart
      ctx.save()
      ctx.strokeStyle = getStyle('--color-accent-yellow')
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(bar.x - 10, bar.y)
      ctx.lineTo(bar.x + 10, bar.y)
      ctx.stroke()
      ctx.restore()
    })
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

async function renderChart() {
  await nextTick()
  chartInstance.value?.destroy()

  const ctx = chartCanvas.value?.getContext('2d')
  if (!ctx) return

  const { labels, displayData } = getDisplaySeries()
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
  const normalizedExpenses = expenses.map((value) => (value === 0 ? 0 : -value))

  const incomeColor = getStyle('--color-accent-green') || '#22c55e'
  const expenseColor = getStyle('--color-accent-red') || '#ef4444'
  const netColor = getStyle('--color-accent-yellow') || '#eab308'
  const averageIncomeColor = emphasizeColor(incomeColor, 'g')
  const averageExpensesColor = emphasizeColor(expenseColor, 'r')
  const comparisonColor = getStyle('--color-accent-blue') || '#719cd6'
  const sevenDayColor = getStyle('--color-accent-cyan') || '#63cdcf'
  const thirtyDayColor = getStyle('--color-accent-purple') || '#9d79d6'
  const fontFamily = getStyle('--font-chart') || 'ui-sans-serif, system-ui, sans-serif'

  const datasets = [
    {
      type: 'bar',
      label: 'Expenses',
      data: normalizedExpenses,
      barThickness: 18,
      backgroundColor: expenseColor,
      borderColor: expenseColor,
      borderWidth: 1,
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
      order: 2,
    },
    {
      type: 'line',
      label: 'Net',
      data: net,
      borderColor: netColor,
      backgroundColor: 'transparent',
      borderWidth: 2,
      tension: 0.25,
      pointRadius: 0,
      netIndicator: true,
      order: 3,
    },
  ]

  if (showAvgIncome.value)
    datasets.push(
      buildLineDataset(
        'Avg Income',
        labels.map(() => income.reduce((a, b) => a + b, 0) / income.length),
        averageIncomeColor,
        { borderDash: [6, 6], order: 4 },
      ),
    )

  if (showAvgExpenses.value)
    datasets.push(
      buildLineDataset(
        'Avg Expenses',
        labels.map(() => expenses.reduce((a, b) => a + b, 0) / expenses.length),
        averageExpensesColor,
        { borderDash: [4, 8], order: 5 },
      ),
    )

  if (showComparisonOverlay.value) {
    const ctx = buildComparisonContext()
    const series = buildComparisonSeries(labels, comparisonData.value, ctx)
    const comparisonLabel =
      ctx?.mode === 'prior_month_to_date' ? 'Prior month to-date' : 'Previous 30 days'
    datasets.push(
      buildLineDataset(comparisonLabel, series, comparisonColor, {
        borderDash: [2, 6],
        order: 6,
      }),
    )
  }

  if (show30Day.value)
    datasets.push(
      buildLineDataset('30-Day Avg', movingAverage(net, 30), thirtyDayColor, {
        borderDash: [8, 4],
        borderWidth: 3,
        order: 7,
      }),
    )

  if (show7Day.value)
    datasets.push(
      buildLineDataset('7-Day Avg', movingAverage(net, 7), sevenDayColor, {
        borderDash: [2, 2],
        borderWidth: 3,
        order: 8,
      }),
    )

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    plugins: [netLinePlugin],
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      onClick: handleBarClick,
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
          mode: 'nearest',
          intersect: true,
          titleColor: getStyle('--color-accent-yellow'),
          bodyColor: getStyle('--color-text-light'),
          titleFont: { family: "'Fira Code', monospace", weight: '600' },
          bodyFont: { family: "'Fira Code', monospace" },
          cornerRadius: 10,
          caretPadding: 8,
          caretSize: 7,
          bodySpacing: 6,
          titleSpacing: 4,
          titleMarginBottom: 6,
          position: 'netDash',
        },
      },
    },
  })
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
