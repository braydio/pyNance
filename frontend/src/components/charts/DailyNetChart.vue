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
  const currentStart = new Date(end)
  currentStart.setDate(end.getDate() - 29)

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

const netLinePlugin = {
  id: 'netLinePlugin',
  afterDatasetsDraw(chart) {
    const idx = chart.data.datasets.findIndex((d) => d.label === 'Net')
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

  const fullLabels = buildDateRangeLabels(
    requestRange.value.startDate || labels[0],
    requestRange.value.endDate || labels.at(-1),
  )
  const fullNet = padDailyNetData(chartData.value, fullLabels).map((d) => d.net.parsedValue)

  const ma7 = labels.map((l) => movingAverage(fullNet, 7)[fullLabels.indexOf(l)] ?? null)
  const ma30 = labels.map((l) => movingAverage(fullNet, 30)[fullLabels.indexOf(l)] ?? null)

  const avgIncome = income.length ? income.reduce((a, b) => a + b, 0) / income.length : 0
  const avgExpenses = expenses.length ? expenses.reduce((a, b) => a + b, 0) / expenses.length : 0

  const datasets = [
    { type: 'bar', label: 'Income', data: income, barThickness: 20 },
    { type: 'bar', label: 'Expenses', data: expenses, barThickness: 20 },
    { type: 'bar', label: 'Net', data: net, backgroundColor: 'transparent', barThickness: 20 },
  ]

  if (showAvgIncome.value)
    datasets.push({ type: 'line', label: 'Avg Income', data: labels.map(() => avgIncome) })
  if (showAvgExpenses.value)
    datasets.push({ type: 'line', label: 'Avg Expenses', data: labels.map(() => avgExpenses) })
  if (show7Day.value) datasets.push({ type: 'line', label: '7-Day Avg', data: ma7 })
  if (show30Day.value) datasets.push({ type: 'line', label: '30-Day Avg', data: ma30 })

  if (showComparisonOverlay.value) {
    const ctx = buildComparisonContext()
    const series = buildComparisonSeries(labels, comparisonData.value, ctx)
    if (series.some((v) => v !== null))
      datasets.push({ type: 'line', label: 'Comparison', data: series })
  }

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    plugins: [netLinePlugin],
    data: { labels, datasets },
    options: { responsive: true, maintainAspectRatio: false, onClick: handleBarClick },
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
watch(() => [comparisonMode.value, showComparisonOverlay.value], fetchComparisonData)

onMounted(() => {
  fetchData()
  fetchComparisonData()
})
onUnmounted(() => chartInstance.value?.destroy())
</script>
