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
const requestRange = ref({ startDate: null, endDate: null })

const MS_PER_DAY = 24 * 60 * 60 * 1000

const getStyle = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()

const formatDateKey = (d) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(
    2,
    '0',
  )}`

const parseDateKey = (s) => (s ? new Date(`${s}T00:00:00`) : null)

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

/**
 * Calculate a trailing moving average that gracefully handles sparse leading data.
 *
 * @param {number[]} values - Series to smooth.
 * @param {number} window - Window size in days.
 * @returns {number[]} Moving average series.
 */
function movingAverage(values, window) {
  if (!values.length) return []

  return values.map((_, i) => {
    const start = Math.max(0, i - window + 1)
    const slice = values.slice(start, i + 1)
    const divisor = Math.min(window, slice.length)
    const sum = slice.reduce((a, b) => a + b, 0)
    return divisor ? sum / divisor : 0
  })
}

function getActiveDateRange() {
  if (!props.zoomedOut) return props
  const end = new Date()
  const start = new Date()
  start.setMonth(start.getMonth() - 6)
  return { startDate: formatDateKey(start), endDate: formatDateKey(end) }
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

function buildComparisonSeries(labels, data, ctx) {
  if (!ctx) return []

  if (ctx.mode === 'prior_month_to_date') {
    const byDay = new Map()
    data.forEach((d) => byDay.set(new Date(d.date).getDate(), d.net.parsedValue))
    return labels.map((l) => byDay.get(new Date(l).getDate()) ?? null)
  }

  const byIndex = new Map()
  data.forEach((d) => {
    const idx = Math.floor((new Date(d.date) - ctx.priorStart) / MS_PER_DAY)
    if (idx >= 0 && idx < 30) byIndex.set(idx, d.net.parsedValue)
  })

  return labels.map((l) => {
    const idx = Math.floor((new Date(l) - ctx.currentStart) / MS_PER_DAY)
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

async function renderChart() {
  await nextTick()
  if (chartInstance.value) chartInstance.value.destroy()

  const ctx = chartCanvas.value?.getContext('2d')
  if (!ctx) return

  const { startDate, endDate } = getActiveDateRange()
  const labels = buildDateRangeLabels(startDate, endDate)
  const displayData = padDailyNetData(chartData.value, labels)

  const net = displayData.map((d) => d.net.parsedValue)
  const income = displayData.map((d) => d.income.parsedValue)
  const expenses = displayData.map((d) => d.expenses.parsedValue)

  const fullLabels = buildDateRangeLabels(requestRange.value.startDate, requestRange.value.endDate)

  const fullNet = padDailyNetData(chartData.value, fullLabels).map((d) => d.net.parsedValue)

  const ma7Full = movingAverage(fullNet, 7)
  const ma30Full = movingAverage(fullNet, 30)

  const idx = Object.fromEntries(fullLabels.map((l, i) => [l, i]))
  const ma7 = labels.map((l, index) => {
    const value = ma7Full[idx[l]]
    if (value !== undefined && value !== null) return value
    const start = Math.max(0, index - 6)
    const slice = net.slice(start, index + 1)
    return slice.length ? slice.reduce((a, b) => a + b, 0) / Math.min(7, slice.length) : 0
  })
  const ma30 = labels.map((l, index) => {
    const value = ma30Full[idx[l]]
    if (value !== undefined && value !== null) return value
    const start = Math.max(0, index - 29)
    const slice = net.slice(start, index + 1)
    return slice.length ? slice.reduce((a, b) => a + b, 0) / Math.min(30, slice.length) : 0
  })

  const avgIncome = income.reduce((a, b) => a + b, 0) / income.length
  const avgExpenses = expenses.reduce((a, b) => a + b, 0) / expenses.length

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
    { type: 'line', label: 'Net', data: net, borderWidth: 2, pointRadius: 0 },
  ]

  if (props.show7Day) {
    datasets.push({ type: 'line', label: '7-Day Avg', data: ma7, borderWidth: 2, pointRadius: 0 })
  }
  if (props.show30Day) {
    datasets.push({
      type: 'line',
      label: '30-Day Avg',
      data: ma30,
      borderWidth: 2,
      pointRadius: 0,
    })
  }

  if (props.showComparisonOverlay) {
    const ctx = buildComparisonContext()
    const comparisonSeries = buildComparisonSeries(labels, comparisonData.value, ctx)
    datasets.push({
      type: 'line',
      label: 'Prior month to-date',
      data: comparisonSeries,
      borderWidth: 1,
      borderDash: [5, 5],
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
  emit('data-change', displayData)
}

async function fetchData() {
  const start = new Date(props.startDate)
  start.setDate(start.getDate() - 30)

  const params = {
    start_date: formatDateKey(start),
    end_date: props.endDate,
  }

  requestRange.value = params
  const res = await fetchDailyNet(params)
  if (res.status === 'success') chartData.value = res.data

  if (props.showComparisonOverlay) {
    const ctx = buildComparisonContext()
    if (ctx?.priorStart && ctx?.priorEnd) {
      const comparisonRes = await fetchDailyNet({
        start_date: formatDateKey(ctx.priorStart),
        end_date: formatDateKey(ctx.priorEnd),
      })
      if (comparisonRes.status === 'success') comparisonData.value = comparisonRes.data
    }
  } else {
    comparisonData.value = []
  }
}

watch([chartData, comparisonData, show7Day, show30Day, showAvgIncome, showAvgExpenses], renderChart)
watch(
  () => [props.startDate, props.endDate, props.zoomedOut, props.showComparisonOverlay, props.comparisonMode],
  fetchData,
)

onMounted(fetchData)
onUnmounted(() => chartInstance.value?.destroy())
</script>
