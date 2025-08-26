<template>
  <div class="daily-net-chart">
    <div style="height: 400px">
      <canvas ref="chartCanvas" style="width: 100%; height: 100%"></canvas>
    </div>
  </div>
</template>

<script setup>
// Displays income, expenses, and net totals for the selected date range.
// Accepts start and end dates along with a zoom toggle for aggregated view.
// Days exceeding their average are highlighted with a slightly intensified hue.
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
})
const { show7Day, show30Day, showAvgIncome, showAvgExpenses } = toRefs(props)
// Emits "bar-click" when a bar is selected, "summary-change" when data totals change, and "data-change" when chart data updates
const emit = defineEmits(['bar-click', 'summary-change', 'data-change'])

const chartInstance = ref(null)
const chartCanvas = ref(null)
const chartData = ref([])

function getStyle(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
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
  // Calculate moving averages from the complete dataset so trend lines aren't
  // truncated by the date filter.
  const allNetValues = chartData.value.map((item) => item.net.parsedValue)
  const ma7Full = movingAverage(allNetValues, 7)
  const ma30Full = movingAverage(allNetValues, 30)

  const labels = filtered.length ? filtered.map((item) => item.date) : [' ']
  // Extract numeric values from response objects for the filtered range
  const netValues = filtered.length ? filtered.map((item) => item.net.parsedValue) : [0]
  const incomeValues = filtered.length ? filtered.map((item) => item.income.parsedValue) : [0]
  const expenseValues = filtered.length ? filtered.map((item) => item.expenses.parsedValue) : [0]
  // Expenses are already negative (parsedValue); use as is for chart

  // Lookup table to align moving averages with filtered labels
  const indexByDate = chartData.value.reduce((acc, item, idx) => {
    acc[item.date] = idx
    return acc
  }, {})
  const ma7 = filtered.map((item) => ma7Full[indexByDate[item.date]])
  const ma30 = filtered.map((item) => ma30Full[indexByDate[item.date]])

  const avgIncome = incomeValues.length
    ? incomeValues.reduce((a, b) => a + b, 0) / incomeValues.length
    : 0
  const avgExpenses = expenseValues.length
    ? expenseValues.reduce((a, b) => a + b, 0) / expenseValues.length
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
              return filtered[idx]?.date || tooltipItems[0].label
            },
            // Suppress default per-dataset labels
            label: () => null,
            // After title, display income, expenses, net, and transactions
            afterBody: (tooltipItems) => {
              const idx = tooltipItems[0].dataIndex
              const rec = filtered[idx]
              if (!rec) return []
              return [
                `Income: ${formatAmount(rec.income.parsedValue)}`,
                `Expenses: ${formatAmount(rec.expenses.parsedValue)}`,
                `Net: ${formatAmount(rec.net.parsedValue)}`,
                `Transactions: ${rec.transaction_count}`,
              ]
            },
          },
          backgroundColor: getStyle('--theme-bg'),
          titleColor: getStyle('--color-accent-yellow'),
          bodyColor: getStyle('--color-text-light'),
          borderColor: getStyle('--color-accent-yellow'),
          borderWidth: 1,
        },
        // No legend needed with inline net lines
        legend: { display: false },
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
            // Show one label per week, formatted as Mon DD
            callback: (value, index) => {
              // Only show one label per week
              if (index % 7 !== 0) return ''
              // Use the original label (YYYY-MM-DD) for accurate parsing
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

function updateSummary() {
  const filtered = filterDataByRange(chartData.value)
  const totalIncome = filtered.reduce((sum, d) => sum + (d.income?.parsedValue || 0), 0)
  const totalExpenses = filtered.reduce((sum, d) => sum + (d.expenses?.parsedValue || 0), 0)
  const totalNet = filtered.reduce((sum, d) => sum + (d.net?.parsedValue || 0), 0)

  emit('summary-change', {
    totalIncome,
    totalExpenses,
    totalNet,
  })

  // Also emit the filtered chart data for the statistics component
  emit('data-change', filtered)
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
  ],
  async () => {
    updateSummary()
    await renderChart()
  },
)

watch(() => [props.startDate, props.endDate, props.zoomedOut], fetchData)

onMounted(() => {
  fetchData()
})

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.destroy()
    chartInstance.value = null
  }
})
</script>
