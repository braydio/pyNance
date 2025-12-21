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
 * Accepts start and end dates along with a zoom toggle for aggregated view.
 * X-axis labels scale automatically so extended ranges remain legible.
 * Days exceeding their average are highlighted with a slightly intensified hue.
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
// Emits "bar-click" when a bar is selected, "summary-change" when data totals change, and "data-change" when chart data updates
const emit = defineEmits(['bar-click', 'summary-change', 'data-change'])

const chartInstance = ref(null)
const chartCanvas = ref(null)
const chartData = ref([])
const comparisonData = ref([])
const MS_PER_DAY = 24 * 60 * 60 * 1000

function getStyle(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

/**
 * Format a Date object into YYYY-MM-DD without timezone shifts.
 *
 * @param {Date} date - Date to format.
 * @returns {string} ISO-like date string.
 */
function formatDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
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
 * Generate date labels for every day in the month of the given date string.
 *
 * @param {string} dateString - Reference date in YYYY-MM-DD format.
 * @returns {string[]} Array of date labels covering the full month.
 */
function buildMonthLabels(dateString) {
  const baseDate = parseDateKey(dateString)
  if (!baseDate) return []
  const year = baseDate.getFullYear()
  const month = baseDate.getMonth()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  return Array.from({ length: daysInMonth }, (_, idx) =>
    formatDateKey(new Date(year, month, idx + 1)),
  )
}

/**
 * Create a placeholder daily net entry for dates without data.
 *
 * @param {string} label - Date label for the placeholder entry.
 * @returns {object} Normalized daily net entry.
 */
function createEmptyDailyNetEntry(label) {
  return {
    date: label,
    income: { parsedValue: 0 },
    expenses: { parsedValue: 0 },
    net: { parsedValue: 0 },
    transaction_count: 0,
  }
}

/**
 * Pad daily net data with placeholders so every label has an entry.
 *
 * @param {Array} data - Data returned from the API for the selected range.
 * @param {string[]} labels - Labels for each day in the month.
 * @returns {Array} Padded data aligned with the labels.
 */
function padDailyNetData(data, labels) {
  const byDate = new Map((data || []).map((entry) => [entry.date, entry]))
  return labels.map((label) => byDate.get(label) ?? createEmptyDailyNetEntry(label))
}

/**
 * Determine the cutoff date for month-to-date summaries.
 *
 * @param {string} endDate - Selected end date in YYYY-MM-DD format.
 * @returns {Date} Date to use as the summary cutoff.
 */
function getMonthToDateCutoff(endDate) {
  const today = new Date()
  const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const parsedEnd = parseDateKey(endDate)
  if (!parsedEnd) return todayStart
  return parsedEnd > todayStart ? todayStart : parsedEnd
}

/**
 * Normalize a comparison end date to local midnight without future dates.
 *
 * @param {string} endDate - Selected end date in YYYY-MM-DD format.
 * @returns {Date} Clamped end date for comparisons.
 */
function getComparisonEndDate(endDate) {
  const today = new Date()
  const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const parsedEnd = parseDateKey(endDate)
  if (!parsedEnd) return todayStart
  return parsedEnd > todayStart ? todayStart : parsedEnd
}

/**
 * Determine the comparison range to request based on the current mode.
 *
 * @returns {object|null} Comparison range metadata for API requests and alignment.
 */
function buildComparisonContext() {
  const currentEnd = getComparisonEndDate(props.endDate)
  if (!currentEnd) return null

  if (comparisonMode.value === 'prior_month_to_date') {
    const priorMonthStart = new Date(currentEnd.getFullYear(), currentEnd.getMonth() - 1, 1)
    const priorMonthLast = new Date(currentEnd.getFullYear(), currentEnd.getMonth(), 0)
    const priorDay = Math.min(currentEnd.getDate(), priorMonthLast.getDate())
    const priorMonthEnd = new Date(
      priorMonthStart.getFullYear(),
      priorMonthStart.getMonth(),
      priorDay,
    )
    return {
      mode: 'prior_month_to_date',
      priorStart: priorMonthStart,
      priorEnd: priorMonthEnd,
    }
  }

  const currentStart = new Date(currentEnd)
  currentStart.setDate(currentStart.getDate() - 29)
  const priorEnd = new Date(currentStart)
  priorEnd.setDate(priorEnd.getDate() - 1)
  const priorStart = new Date(priorEnd)
  priorStart.setDate(priorStart.getDate() - 29)

  return {
    mode: 'last_30_vs_previous_30',
    priorStart,
    priorEnd,
    currentStart,
    currentEnd,
  }
}

/**
 * Apply an alpha channel to a hex or rgb color string.
 *
 * @param {string} color - Base color from theme variables.
 * @param {number} alpha - Opacity value between 0 and 1.
 * @returns {string} Color string with alpha applied.
 */
function applyAlphaToColor(color, alpha) {
  if (color.startsWith('rgb(')) {
    return color.replace('rgb(', 'rgba(').replace(')', `, ${alpha})`)
  }
  if (!color.startsWith('#')) return color

  let normalized = color.replace('#', '')
  if (normalized.length === 3) {
    normalized = normalized
      .split('')
      .map((ch) => ch + ch)
      .join('')
  }
  const hexValue = parseInt(normalized, 16)
  const red = (hexValue >> 16) & 0xff
  const green = (hexValue >> 8) & 0xff
  const blue = hexValue & 0xff
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`
}

/**
 * Align comparison data to the current chart labels.
 *
 * @param {string[]} labels - Current chart labels.
 * @param {Array} data - Comparison dataset from the API.
 * @param {object|null} context - Comparison range metadata.
 * @returns {Array} Aligned comparison net values.
 */
function buildComparisonSeries(labels, data, context) {
  if (!context) return []

  if (context.mode === 'prior_month_to_date') {
    const valuesByDay = new Map()
    ;(data || []).forEach((entry) => {
      const entryDate = parseDateKey(entry?.date)
      if (!entryDate) return
      valuesByDay.set(entryDate.getDate(), entry.net?.parsedValue || 0)
    })

    return labels.map((label) => {
      const labelDate = parseDateKey(label)
      if (!labelDate) return null
      return valuesByDay.get(labelDate.getDate()) ?? null
    })
  }

  const valuesByIndex = new Map()
  ;(data || []).forEach((entry) => {
    const entryDate = parseDateKey(entry?.date)
    if (!entryDate) return
    const index = Math.floor((entryDate - context.priorStart) / MS_PER_DAY)
    if (index < 0 || index > 29) return
    valuesByIndex.set(index, entry.net?.parsedValue || 0)
  })

  return labels.map((label) => {
    const labelDate = parseDateKey(label)
    if (!labelDate || labelDate < context.currentStart || labelDate > context.currentEnd)
      return null
    const index = Math.floor((labelDate - context.currentStart) / MS_PER_DAY)
    return valuesByIndex.get(index) ?? null
  })
}

/**
 * Provide display labels for comparison series.
 *
 * @param {string} mode - Comparison mode key.
 * @returns {string} Human-friendly label.
 */
function getComparisonLabel(mode) {
  if (mode === 'prior_month_to_date') return 'Prior month to-date'
  return 'Last 30 days vs previous 30'
}

function filterDataByRange(data) {
  const now = new Date()
  let start
  if (props.zoomedOut) {
    start = new Date()
    start.setMonth(start.getMonth() - 6)
  } else {
    start = props.startDate ? new Date(props.startDate) : null
    const end = props.endDate ? new Date(props.endDate) : now
    return (data || []).filter((item) => {
      const d = new Date(item.date)
      return (!start || d >= start) && d <= end
    })
  }
  return (data || []).filter((item) => {
    const d = new Date(item.date)
    return d >= start && d <= now
  })
}

/**
 * Build display-ready labels and data, padding empty days for full month views.
 *
 * @param {Array} filteredData - API data filtered to the selected range.
 * @returns {{ labels: string[], displayData: Array }} Labels and aligned data.
 */
function getDisplaySeries(filteredData) {
  if (!props.zoomedOut) {
    const referenceDate = props.startDate || props.endDate
    const labels = buildMonthLabels(referenceDate)
    if (labels.length) {
      return { labels, displayData: padDailyNetData(filteredData, labels) }
    }
  }

  return {
    labels: filteredData.length ? filteredData.map((item) => item.date) : [' '],
    displayData: filteredData,
  }
}

// Emit the selected date when a bar is clicked
function handleBarClick(evt) {
  if (!chartInstance.value) return
  const points = chartInstance.value.getElementsAtEventForMode(
    evt,
    'nearest',
    { intersect: true },
    false,
  )
  if (points.length) {
    const index = points[0].index
    const date = chartInstance.value.data.labels[index]
    emit('bar-click', date)
  }
}

// Plugin to draw a thin net line atop bars
const netLinePlugin = {
  id: 'netLinePlugin',
  afterDatasetsDraw(chart) {
    const { ctx } = chart
    chart.data.datasets.forEach((dataset, idx) => {
      if (dataset.label === 'Net') {
        const meta = chart.getDatasetMeta(idx)
        meta.data.forEach((bar) => {
          const y = bar.y
          const x = bar.x
          // use configured barThickness for width
          const width = dataset.barThickness || 0
          ctx.save()
          ctx.strokeStyle = getStyle('--color-accent-yellow')
          ctx.lineWidth = 2
          ctx.beginPath()
          ctx.moveTo(x - width / 2, y)
          ctx.lineTo(x + width / 2, y)
          ctx.stroke()
          ctx.restore()
        })
      }
    })
  },
}

/**
 * Slightly intensify the specified color channel of a hex color.
 *
 * @param {string} hex - Base color as a hexadecimal string.
 * @param {'r' | 'g'} channel - Color channel to emphasize.
 * @returns {string} Hex color string with adjusted channel.
 */
function emphasizeColor(hex, channel) {
  let normalizedHex = hex.replace('#', '')
  if (normalizedHex.length === 3)
    normalizedHex = normalizedHex
      .split('')
      .map((ch) => ch + ch)
      .join('')
  const colorNumber = parseInt(normalizedHex, 16)
  let redChannel = (colorNumber >> 16) & 0xff
  let greenChannel = (colorNumber >> 8) & 0xff
  let blueChannel = colorNumber & 0xff
  const adjustment = 20
  if (channel === 'r') {
    redChannel = Math.min(255, redChannel + adjustment)
    greenChannel = Math.max(0, greenChannel - adjustment)
    blueChannel = Math.max(0, blueChannel - adjustment)
  } else if (channel === 'g') {
    greenChannel = Math.min(255, greenChannel + adjustment)
    redChannel = Math.max(0, redChannel - adjustment)
    blueChannel = Math.max(0, blueChannel - adjustment)
  }
  return `#${((redChannel << 16) | (greenChannel << 8) | blueChannel)
    .toString(16)
    .padStart(6, '0')}`
}

function movingAverage(values, window) {
  const result = []
  for (let i = 0; i < values.length; i++) {
    if (i < window - 1) {
      result.push(null)
    } else {
      const slice = values.slice(i - window + 1, i + 1)
      const sum = slice.reduce((a, b) => a + b, 0)
      result.push(sum / window)
    }
  }
  return result
}

async function renderChart() {
  await nextTick()
  const canvasEl = chartCanvas.value
  if (!canvasEl) {
    console.warn('Chart canvas not ready!')
    return
  }
  const ctx = canvasEl.getContext('2d')
  if (!ctx) {
    console.warn('Chart context not available!')
    return
  }
  if (chartInstance.value) {
    chartInstance.value.destroy()
    chartInstance.value = null
  }

  const filtered = filterDataByRange(chartData.value)
  const { labels, displayData } = getDisplaySeries(filtered)
  const hasDisplayData = displayData.length > 0
  const comparisonContext = showComparisonOverlay.value ? buildComparisonContext() : null
  const comparisonSeries = showComparisonOverlay.value
    ? buildComparisonSeries(labels, comparisonData.value, comparisonContext)
    : []
  // Calculate moving averages from the complete dataset so trend lines aren't
  // truncated by the date filter.
  const allNetValues = chartData.value.map((item) => item.net.parsedValue)
  const ma7Full = movingAverage(allNetValues, 7)
  const ma30Full = movingAverage(allNetValues, 30)

  // Determine how frequently to display x-axis labels so long ranges remain readable
  const tickInterval = Math.max(1, Math.ceil(labels.length / 14))
  // Extract numeric values from response objects for the filtered range
  const netValues = hasDisplayData ? displayData.map((item) => item.net?.parsedValue || 0) : [0]
  const incomeValues = hasDisplayData
    ? displayData.map((item) => item.income?.parsedValue || 0)
    : [0]
  const expenseValues = hasDisplayData
    ? displayData.map((item) => item.expenses?.parsedValue || 0)
    : [0]
  // Expenses are already negative (parsedValue); use as is for chart

  // Lookup table to align moving averages with filtered labels
  const indexByDate = chartData.value.reduce((acc, item, idx) => {
    acc[item.date] = idx
    return acc
  }, {})
  const ma7 = labels.map((label) =>
    indexByDate[label] === undefined ? null : ma7Full[indexByDate[label]],
  )
  const ma30 = labels.map((label) =>
    indexByDate[label] === undefined ? null : ma30Full[indexByDate[label]],
  )

  const actualIncomeValues = filtered.map((item) => item.income?.parsedValue || 0)
  const actualExpenseValues = filtered.map((item) => item.expenses?.parsedValue || 0)
  const avgIncome = actualIncomeValues.length
    ? actualIncomeValues.reduce((a, b) => a + b, 0) / actualIncomeValues.length
    : 0
  const avgExpenses = actualExpenseValues.length
    ? actualExpenseValues.reduce((a, b) => a + b, 0) / actualExpenseValues.length
    : 0

  const incomeBase = getStyle('--color-accent-green')
  const expenseBase = getStyle('--color-accent-red')
  const incomeColors = incomeValues.map((v) =>
    v > avgIncome ? emphasizeColor(incomeBase, 'g') : incomeBase,
  )
  const expenseColors = expenseValues.map((v) =>
    Math.abs(v) > Math.abs(avgExpenses) ? emphasizeColor(expenseBase, 'r') : expenseBase,
  )

  const datasets = [
    {
      type: 'bar',
      label: 'Income',
      data: incomeValues,
      backgroundColor: incomeColors,
      borderRadius: 4,
      barThickness: 20,
    },
    {
      type: 'bar',
      label: 'Expenses',
      data: expenseValues,
      backgroundColor: expenseColors,
      borderRadius: 4,
      barThickness: 20,
    },
    // Net dataset placeholder for plugin drawing
    {
      type: 'bar',
      label: 'Net',
      data: netValues,
      backgroundColor: 'transparent',
      borderWidth: 0,
      barThickness: 20,
    },
  ]

  if (showAvgIncome.value) {
    datasets.push({
      type: 'line',
      label: 'Avg Income',
      data: labels.map(() => avgIncome),
      borderColor: getStyle('--color-accent-green'),
      borderDash: [4, 4],
      borderWidth: 1,
      pointRadius: 0,
      order: 1, // ensure line renders above bars
    })
  }

  if (showAvgExpenses.value) {
    datasets.push({
      type: 'line',
      label: 'Avg Expenses',
      data: labels.map(() => avgExpenses),
      borderColor: getStyle('--color-accent-red'),
      borderDash: [4, 4],
      borderWidth: 1,
      pointRadius: 0,
      order: 1, // ensure line renders above bars
    })
  }

  if (show7Day.value) {
    datasets.push({
      type: 'line',
      label: '7-Day Avg',
      data: ma7,
      borderColor: getStyle('--color-accent-orange'),
      borderWidth: 2,
      pointRadius: 0,
      order: 1, // ensure line renders above bars
    })
  }

  if (show30Day.value) {
    datasets.push({
      type: 'line',
      label: '30-Day Avg',
      data: ma30,
      borderColor: getStyle('--color-accent-blue'),
      borderWidth: 2,
      pointRadius: 0,
      order: 1, // ensure line renders above bars
    })
  }

  if (showComparisonOverlay.value && comparisonSeries.some((value) => value !== null)) {
    datasets.push({
      type: 'line',
      label: getComparisonLabel(comparisonMode.value),
      data: comparisonSeries,
      borderColor: applyAlphaToColor(getStyle('--color-accent-purple'), 0.45),
      borderDash: [6, 4],
      borderWidth: 2,
      pointRadius: 0,
      order: 1, // ensure line renders above bars
    })
  }

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    // include netLinePlugin to draw net lines
    plugins: [netLinePlugin],
    data: {
      labels,
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 20, bottom: 8 } },
      plugins: {
        tooltip: {
          callbacks: {
            // Show the date as title
            title: (tooltipItems) => {
              const idx = tooltipItems[0].dataIndex
              return displayData[idx]?.date || tooltipItems[0].label
            },
            // Suppress default per-dataset labels
            label: () => null,
            // After title, display income, expenses, net, and transactions
            afterBody: (tooltipItems) => {
              const idx = tooltipItems[0].dataIndex
              const rec = displayData[idx]
              if (!rec) {
                return [
                  `Income: ${formatAmount(0)}`,
                  `Expenses: ${formatAmount(0)}`,
                  `Net: ${formatAmount(0)}`,
                  `Transactions: 0`,
                ]
              }
              return [
                `Income: ${formatAmount(rec.income?.parsedValue || 0)}`,
                `Expenses: ${formatAmount(rec.expenses?.parsedValue || 0)}`,
                `Net: ${formatAmount(rec.net?.parsedValue || 0)}`,
                `Transactions: ${rec.transaction_count ?? 0}`,
              ]
            },
          },
          backgroundColor: getStyle('--theme-bg'),
          titleColor: getStyle('--color-accent-yellow'),
          bodyColor: getStyle('--color-text-light'),
          borderColor: getStyle('--color-accent-yellow'),
          borderWidth: 1,
        },
        legend: {
          display: false,
          labels: { color: getStyle('--color-text-muted') },
        },
      },
      scales: {
        y: {
          min: Math.min(...expenseValues, 0),
          max: Math.max(...incomeValues, 0),
          grid: { display: true, color: getStyle('--divider') },
          ticks: {
            callback: (value) => formatAmount(value),
            color: getStyle('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 14 },
          },
        },
        x: {
          display: true,
          stacked: true,
          grid: { display: true, color: getStyle('--divider') },
          ticks: {
            autoSkip: false,
            maxTicksLimit: 14,
            // Dynamically space labels to keep the axis legible across large date ranges
            callback: (value, index) => {
              if (index % tickInterval !== 0) return ''
              const raw = labels[index]
              if (!raw) return ''
              const dt = new Date(raw)
              if (isNaN(dt)) return raw
              // Format e.g. "Jul 05"
              return dt.toLocaleDateString(undefined, { month: 'short', day: '2-digit' })
            },
            color: getStyle('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 14 },
          },
        },
      },
      onClick: handleBarClick,
    },
  })
}

async function fetchData() {
  try {
    const params = {}
    if (props.zoomedOut) {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 6)
      // fetch an extra month of data for trendline calculations
      start.setDate(start.getDate() - 30)
      params.start_date = start.toISOString().slice(0, 10)
      params.end_date = end.toISOString().slice(0, 10)
    } else {
      const start = new Date(props.startDate)
      // include prior days so moving averages use the full expected range
      start.setDate(start.getDate() - 30)
      params.start_date = start.toISOString().slice(0, 10)
      params.end_date = props.endDate
    }
    const response = await fetchDailyNet(params)
    if (response.status === 'success') {
      chartData.value = response.data
    }
  } catch (error) {
    console.error('Error fetching daily net data:', error)
  }
}

/**
 * Fetch comparison data for the selected overlay mode.
 */
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
    const params = {
      start_date: formatDateKey(context.priorStart),
      end_date: formatDateKey(context.priorEnd),
    }
    const response = await fetchDailyNet(params)
    if (response.status === 'success') {
      comparisonData.value = response.data
    }
  } catch (error) {
    console.error('Error fetching comparison net data:', error)
    comparisonData.value = []
  }
}

function updateSummary() {
  const filtered = filterDataByRange(chartData.value)
  const summaryCutoff = props.zoomedOut ? null : getMonthToDateCutoff(props.endDate)
  const summaryData = summaryCutoff
    ? filtered.filter((entry) => {
        const entryDate = parseDateKey(entry?.date)
        return entryDate ? entryDate <= summaryCutoff : false
      })
    : filtered
  const totalIncome = summaryData.reduce((sum, d) => sum + (d.income?.parsedValue || 0), 0)
  const totalExpenses = summaryData.reduce((sum, d) => sum + (d.expenses?.parsedValue || 0), 0)
  const totalNet = summaryData.reduce((sum, d) => sum + (d.net?.parsedValue || 0), 0)

  emit('summary-change', {
    totalIncome,
    totalExpenses,
    totalNet,
  })

  // Also emit the filtered chart data for the statistics component
  emit('data-change', summaryData)
}

watch(
  [
    chartData,
    () => props.zoomedOut,
    () => props.startDate,
    () => props.endDate,
    show7Day,
    show30Day,
    showAvgIncome,
    showAvgExpenses,
    showComparisonOverlay,
    comparisonMode,
    comparisonData,
  ],
  async () => {
    updateSummary()
    await renderChart()
  },
)

watch(() => [props.startDate, props.endDate, props.zoomedOut], fetchData)
watch(
  () => [
    props.startDate,
    props.endDate,
    props.zoomedOut,
    showComparisonOverlay.value,
    comparisonMode.value,
  ],
  fetchComparisonData,
)

onMounted(() => {
  fetchData()
  fetchComparisonData()
})

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.destroy()
    chartInstance.value = null
  }
})
</script>
