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
  displayStartDate: { type: String, default: '' },
  displayEndDate: { type: String, default: '' },
  rangeMode: { type: String, default: 'custom' },
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
  rangeMode,
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

/**
 * Determine the month boundaries for a given date.
 *
 * @param {Date} referenceDate - Date used to derive the month range.
 * @returns {{ start: Date, end: Date }} First and last dates of the month.
 */
function getMonthBounds(referenceDate) {
  return {
    start: new Date(referenceDate.getFullYear(), referenceDate.getMonth(), 1),
    end: new Date(referenceDate.getFullYear(), referenceDate.getMonth() + 1, 0),
  }
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

/**
 * Return the display range for the chart (labels), honoring the active preset.
 *
 * @returns {{ startDate: string, endDate: string }} Display range for labels.
 */
function getDisplayRange() {
  const start = props.displayStartDate || props.startDate
  const end = props.displayEndDate || props.endDate

  if (rangeMode.value === 'month_to_date') {
    const startDate = parseDateKey(start)
    if (startDate) {
      const { end: monthEnd } = getMonthBounds(startDate)
      return { startDate: formatDateKey(startDate), endDate: formatDateKey(monthEnd) }
    }
  }

  return { startDate: start, endDate: end }
}

function getActiveDateRange() {
  if (props.zoomedOut) {
    const end = parseDateKey(props.endDate) ?? new Date()
    const start = new Date(end)
    start.setMonth(start.getMonth() - 6)
    return { startDate: formatDateKey(start), endDate: formatDateKey(end) }
  }
  return getDisplayRange()
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

function buildComparisonSeries(labels, data, ctx, { limitToDayOfMonth } = {}) {
  if (!ctx) return []

  if (ctx.mode === 'prior_month_to_date') {
    const byDay = new Map()
    data.forEach((d) => byDay.set(new Date(d.date).getDate(), d.net.parsedValue))
    return labels.map((l) => {
      const day = new Date(l).getDate()
      if (limitToDayOfMonth && day > limitToDayOfMonth) return null
      return byDay.get(day) ?? null
    })
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

/**
 * Emit summary totals for the active input window alongside raw data.
 */
function emitSummary() {
  const start = parseDateKey(props.startDate)
  const end = parseDateKey(props.endDate)
  const totals = chartData.value.reduce(
    (acc, entry) => {
      const entryDate = parseDateKey(entry.date)
      if (!start || !end || !entryDate || entryDate < start || entryDate > end) return acc
      acc.totalIncome += entry.income?.parsedValue ?? 0
      acc.totalExpenses += entry.expenses?.parsedValue ?? 0
      acc.totalNet += entry.net?.parsedValue ?? 0
      return acc
    },
    { totalIncome: 0, totalExpenses: 0, totalNet: 0 },
  )

  emit('summary-change', totals)
  emit('data-change', chartData.value)
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
  const ma7 = labels.map((l) => ma7Full[idx[l]] ?? null)
  const ma30 = labels.map((l) => ma30Full[idx[l]] ?? null)

  const avgIncome = income.length ? income.reduce((a, b) => a + b, 0) / income.length : 0
  const avgExpenses = expenses.length
    ? expenses.reduce((a, b) => a + b, 0) / expenses.length
    : 0

  const incomeBase = getStyle('--color-accent-green')
  const expenseBase = getStyle('--color-accent-red')
  const netColor = getStyle('--color-accent-blue')
  const comparisonColor = getStyle('--color-accent-purple') || '#8b5cf6'

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
      type: 'line',
      label: 'Net',
      data: net,
      borderColor: netColor,
      borderWidth: 2,
      tension: 0.2,
      pointRadius: 0,
    },
  ]

  if (show7Day.value) {
    datasets.push({
      type: 'line',
      label: '7-Day Avg',
      data: ma7,
      borderWidth: 2,
      pointRadius: 0,
      borderDash: [6, 4],
    })
  }

  if (show30Day.value) {
    datasets.push({
      type: 'line',
      label: '30-Day Avg',
      data: ma30,
      borderWidth: 2,
      pointRadius: 0,
      borderDash: [8, 4],
    })
  }

  if (showAvgIncome.value) {
    datasets.push({
      type: 'line',
      label: 'Avg Income',
      data: labels.map(() => avgIncome),
      borderWidth: 1.5,
      pointRadius: 0,
      borderDash: [10, 6],
      borderColor: emphasizeColor(incomeBase, 'g'),
    })
  }

  if (showAvgExpenses.value) {
    datasets.push({
      type: 'line',
      label: 'Avg Expenses',
      data: labels.map(() => avgExpenses),
      borderWidth: 1.5,
      pointRadius: 0,
      borderDash: [10, 6],
      borderColor: expenseBase,
    })
  }

  if (showComparisonOverlay.value) {
    const ctx = buildComparisonContext()
    if (ctx) {
      const comparisonSeries =
        comparisonData.value.length > 0
          ? buildComparisonSeries(labels, comparisonData.value, ctx, {
              limitToDayOfMonth:
                rangeMode.value === 'month_to_date'
                  ? parseDateKey(props.endDate)?.getDate() ?? null
                  : null,
            })
          : labels.map(() => null)

      datasets.push({
        type: 'line',
        label:
          ctx.mode === 'prior_month_to_date' ? 'Prior month to-date' : 'Previous 30 days',
        data: comparisonSeries,
        borderWidth: 2,
        pointRadius: 0,
        borderDash: [4, 4],
        borderColor: comparisonColor,
      })
    }
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

async function fetchData() {
  const start = parseDateKey(props.startDate)
  const end = parseDateKey(props.endDate)
  if (!start || !end) return

  const paddedStart = new Date(start)
  paddedStart.setDate(paddedStart.getDate() - 30)

  const params = {
    start_date: formatDateKey(paddedStart),
    end_date: formatDateKey(end),
  }

  requestRange.value = { startDate: params.start_date, endDate: params.end_date }
  const res = await fetchDailyNet(params)
  chartData.value = res.status === 'success' && Array.isArray(res.data) ? res.data : []

  if (showComparisonOverlay.value) {
    const ctx = buildComparisonContext()
    if (ctx) {
      const comparisonRes = await fetchDailyNet({
        start_date: formatDateKey(ctx.priorStart),
        end_date: formatDateKey(ctx.priorEnd),
      })
      comparisonData.value =
        comparisonRes.status === 'success' && Array.isArray(comparisonRes.data)
          ? comparisonRes.data
          : []
    } else {
      comparisonData.value = []
    }
  } else {
    comparisonData.value = []
  }

  emitSummary()
}

watch(
  [chartData, comparisonData, show7Day, show30Day, showAvgIncome, showAvgExpenses],
  renderChart,
)
watch(
  () => [
    props.startDate,
    props.endDate,
    props.zoomedOut,
    props.showComparisonOverlay,
    props.comparisonMode,
    props.displayStartDate,
    props.displayEndDate,
    props.rangeMode,
  ],
  fetchData,
)
watch(showComparisonOverlay, () => {
  if (!showComparisonOverlay.value) comparisonData.value = []
})

onMounted(fetchData)
onUnmounted(() => chartInstance.value?.destroy())
</script>
