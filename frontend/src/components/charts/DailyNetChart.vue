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

const formatTooltipTitle = (label) => {
  const parsed = parseDateKey(label)
  if (!parsed) return label
  return parsed.toLocaleDateString(undefined, {
    month: 'short',
    day: '2-digit',
    year: 'numeric',
  })
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

const netLinePlugin = {
  id: 'netLinePlugin',
  afterDatasetsDraw(chart) {
    const netIndex = chart.data.datasets.findIndex((dataset) => dataset.label === 'Net')
    if (netIndex === -1) return
    const dataset = chart.data.datasets[netIndex]
    const meta = chart.getDatasetMeta(netIndex)
    const barThickness = dataset.barThickness || 20
    meta.data.forEach((bar) => {
      const { ctx } = chart
      const y = bar.y
      const x = bar.x
      ctx.save()
      ctx.strokeStyle = getStyle('--color-accent-yellow')
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(x - barThickness / 2, y)
      ctx.lineTo(x + barThickness / 2, y)
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
  if (!points.length) return
  const index = points[0].index
  const label = chartInstance.value.data.labels[index]
  if (label) emit('bar-click', label)
}

async function renderChart() {
  await nextTick()
  if (chartInstance.value) {
    chartInstance.value.destroy()
    chartInstance.value = null
  }

  const ctx = chartCanvas.value?.getContext('2d')
  if (!ctx) return

  const { startDate, endDate } = getActiveDateRange()
  const labels = buildDateRangeLabels(startDate, endDate)
  if (!labels.length) return

  const displayData = padDailyNetData(chartData.value, labels)
  updateSummary(displayData)

  const income = displayData.map((d) => d.income.parsedValue)
  const expenses = displayData.map((d) => d.expenses.parsedValue)
  const net = displayData.map((d) => d.net.parsedValue)

  const fullLabels =
    requestRange.value.startDate && requestRange.value.endDate
      ? buildDateRangeLabels(requestRange.value.startDate, requestRange.value.endDate)
      : labels
  const fullNet = padDailyNetData(chartData.value, fullLabels).map((d) => d.net.parsedValue)

  const ma7Full = movingAverage(fullNet, 7)
  const ma30Full = movingAverage(fullNet, 30)
  const lookup = Object.fromEntries(fullLabels.map((l, i) => [l, i]))
  const ma7 = labels.map((label) => (lookup[label] === undefined ? null : ma7Full[lookup[label]]))
  const ma30 = labels.map((label) => (lookup[label] === undefined ? null : ma30Full[lookup[label]]))

  const actualIncomeValues = income.length ? income : [0]
  const actualExpenseValues = expenses.length ? expenses : [0]
  const avgIncome =
    actualIncomeValues.reduce((sum, value) => sum + value, 0) / actualIncomeValues.length
  const avgExpenses =
    actualExpenseValues.reduce((sum, value) => sum + value, 0) / actualExpenseValues.length

  const incomeBase = getStyle('--color-accent-green')
  const expenseBase = getStyle('--color-accent-red')
  const comparisonColor = getStyle('--color-text-muted')

  const incomeColors = income.map((value) =>
    value > avgIncome ? emphasizeColor(incomeBase, 'g') : incomeBase,
  )
  const expenseColors = expenses.map((value) =>
    Math.abs(value) > Math.abs(avgExpenses) ? emphasizeColor(expenseBase, 'r') : expenseBase,
  )

  const datasets = [
    {
      type: 'bar',
      label: 'Income',
      data: income,
      backgroundColor: incomeColors,
      borderRadius: 4,
      barThickness: 20,
    },
    {
      type: 'bar',
      label: 'Expenses',
      data: expenses,
      backgroundColor: expenseColors,
      borderRadius: 4,
      barThickness: 20,
    },
    {
      type: 'bar',
      label: 'Net',
      data: net,
      backgroundColor: 'transparent',
      borderWidth: 0,
      barThickness: 20,
      order: 2,
    },
  ]

  if (showAvgIncome.value) {
    datasets.push({
      type: 'line',
      label: 'Avg Income',
      data: labels.map(() => avgIncome),
      borderColor: emphasizeColor(incomeBase, 'g'),
      borderDash: [6, 6],
      pointRadius: 0,
      order: 1,
    })
  }

  if (showAvgExpenses.value) {
    datasets.push({
      type: 'line',
      label: 'Avg Expenses',
      data: labels.map(() => avgExpenses),
      borderColor: emphasizeColor(expenseBase, 'r'),
      borderDash: [6, 6],
      pointRadius: 0,
      order: 1,
    })
  }

  if (show7Day.value) {
    datasets.push({
      type: 'line',
      label: '7-Day Avg',
      data: ma7,
      borderWidth: 2,
      pointRadius: 0,
      borderColor: getStyle('--color-accent-cyan'),
      order: 1,
    })
  }

  if (show30Day.value) {
    datasets.push({
      type: 'line',
      label: '30-Day Avg',
      data: ma30,
      borderWidth: 2,
      pointRadius: 0,
      borderColor: getStyle('--color-accent-magenta'),
      order: 1,
    })
  }

  const comparisonContext = showComparisonOverlay.value ? buildComparisonContext() : null
  const comparisonSeries =
    comparisonContext && comparisonData.value.length
      ? buildComparisonSeries(labels, comparisonData.value, comparisonContext)
      : []
  if (showComparisonOverlay.value && comparisonSeries.some((value) => value !== null)) {
    datasets.push({
      type: 'line',
      label:
        comparisonContext?.mode === 'prior_month_to_date'
          ? 'Prior Month'
          : 'Previous 30 Days',
      data: comparisonSeries,
      borderColor: comparisonColor,
      borderDash: [4, 6],
      pointRadius: 0,
      borderWidth: 2,
      order: 1,
    })
  }

  const tickInterval = Math.max(1, Math.ceil(labels.length / 14))

  const yValues = [...income, ...expenses]
  const yMin = Math.min(...yValues, 0)
  const yMax = Math.max(...yValues, 0)

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    plugins: [netLinePlugin],
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 20, bottom: 8 } },
      scales: {
        x: {
          stacked: true,
          display: true,
          grid: { display: true, color: getStyle('--divider') },
          ticks: {
            autoSkip: false,
            maxTicksLimit: 14,
            color: getStyle('--color-text-muted'),
            callback: (value, index) => {
              if (index % tickInterval !== 0) return ''
              const label = labels[index]
              if (!label) return ''
              const dt = parseDateKey(label)
              if (!dt) return label
              return dt.toLocaleDateString(undefined, { month: 'short', day: '2-digit' })
            },
          },
        },
        y: {
          min: yMin,
          max: yMax,
          grid: { display: true, color: getStyle('--divider') },
          ticks: {
            callback: (value) => formatAmount(value),
            color: getStyle('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 14 },
          },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          displayColors: true,
          callbacks: {
            title: (items) => {
              const label = items[0]?.label || labels[items[0]?.dataIndex]
              return formatTooltipTitle(label)
            },
            label: () => null,
            afterBody: (items) => {
              const idx = items?.[0]?.dataIndex
              const record = displayData[idx]
              if (!record) return []
              return [
                `Income: ${formatAmount(record.income.parsedValue)}`,
                `Expenses: ${formatAmount(record.expenses.parsedValue)}`,
                `Net: ${formatAmount(record.net.parsedValue)}`,
                `Transactions: ${record.transaction_count ?? 0}`,
              ]
            },
          },
          backgroundColor: getStyle('--theme-bg'),
          titleColor: getStyle('--color-accent-yellow'),
          bodyColor: getStyle('--color-text-light'),
          borderColor: getStyle('--color-accent-yellow'),
          borderWidth: 1,
        },
      },
      onClick: handleBarClick,
    },
  })
}

function updateSummary(displayData) {
  const summary = displayData.reduce(
    (acc, record) => {
      acc.totalIncome += record.income.parsedValue
      acc.totalExpenses += record.expenses.parsedValue
      acc.totalNet += record.net.parsedValue
      return acc
    },
    { totalIncome: 0, totalExpenses: 0, totalNet: 0 },
  )

  emit('summary-change', summary)
  emit('data-change', displayData)
}

function buildFetchParams() {
  if (props.zoomedOut) {
    const end = new Date()
    const start = new Date()
    start.setMonth(start.getMonth() - 6)
    start.setDate(start.getDate() - 30)
    return { start_date: formatDateKey(start), end_date: formatDateKey(end) }
  }

  const end = parseDateKey(props.endDate) ?? new Date()
  const paddedStart = parseDateKey(props.startDate) ?? new Date()
  paddedStart.setDate(paddedStart.getDate() - 30)
  return { start_date: formatDateKey(paddedStart), end_date: formatDateKey(end) }
}

async function fetchData() {
  const params = buildFetchParams()
  requestRange.value = { startDate: params.start_date, endDate: params.end_date }
  try {
    const res = await fetchDailyNet(params)
    if (res.status === 'success') {
      chartData.value = res.data
    }
  } catch (error) {
    console.error('Error fetching daily net data:', error)
  }
}

async function fetchComparisonData() {
  if (!showComparisonOverlay.value) {
    comparisonData.value = []
    return
  }

  const context = buildComparisonContext()
  if (!context) {
    comparisonData.value = []
    return
  }

  try {
    const comparisonParams = {
      start_date: formatDateKey(context.priorStart),
      end_date: formatDateKey(context.priorEnd),
    }
    const comparisonRes = await fetchDailyNet(comparisonParams)
    if (comparisonRes.status === 'success') {
      comparisonData.value = comparisonRes.data
    }
  } catch (error) {
    console.error('Error fetching comparison data:', error)
    comparisonData.value = []
  }
}

watch(
  [
    chartData,
    comparisonData,
    show7Day,
    show30Day,
    showAvgIncome,
    showAvgExpenses,
    showComparisonOverlay,
    comparisonMode,
  ],
  () => {
    renderChart()
  },
)

watch(
  () => [props.startDate, props.endDate, props.zoomedOut],
  () => {
    fetchData()
    fetchComparisonData()
  },
)

watch(
  () => [comparisonMode.value, showComparisonOverlay.value],
  () => {
    fetchComparisonData()
  },
)

onMounted(() => {
  fetchData()
  fetchComparisonData()
})

onUnmounted(() => chartInstance.value?.destroy())
</script>
