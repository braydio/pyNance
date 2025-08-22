<template>
  <div class="daily-net-chart">
    <div class="chart-controls">
      <label><input type="checkbox" v-model="show7Day" /> 7d trend</label>
      <label><input type="checkbox" v-model="show30Day" /> 30d trend</label>
      <label><input type="checkbox" v-model="showAvgIncome" /> avg income</label>
      <label><input type="checkbox" v-model="showAvgExpenses" /> avg expenses</label>
    </div>
    <div style="height: 400px;">
      <canvas ref="chartCanvas" style="width: 100%; height: 100%;"></canvas>
    </div>
  </div>
</template>

<script setup>
// Displays income, expenses, and net totals for recent days. Expenses
// are rendered as negative values so that red bars extend below the
// X-axis while green income bars remain above it.
import { fetchDailyNet } from '@/api/charts'
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Chart } from 'chart.js/auto'
import { formatAmount } from "@/utils/format"

const props = defineProps({ zoomedOut: { type: Boolean, default: false } })
// Emits "bar-click" when a bar is selected, "summary-change" when data totals change, and "data-change" when chart data updates
const emit = defineEmits(['bar-click', 'summary-change', 'data-change'])

const chartInstance = ref(null)
const chartCanvas = ref(null)
const chartData = ref([])
const show7Day = ref(false)
const show30Day = ref(false)
const showAvgIncome = ref(false)
const showAvgExpenses = ref(false)
// Counts of days exceeding their respective averages; used for summary and chart annotations
const aboveAvgIncomeDays = ref(0)
const aboveAvgExpenseDays = ref(0)

function getStyle(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

function filterDataByRange(data) {
  const now = new Date()
  const start = new Date()
  if (!props.zoomedOut) {
    start.setMonth(start.getMonth() - 1)
  } else {
    start.setMonth(start.getMonth() - 6)
  }
  return (data || []).filter(item => {
    const d = new Date(item.date)
    return d >= start && d <= now
  })
}

// Emit the selected date when a bar is clicked
function handleBarClick(evt) {
  if (!chartInstance.value) return
  const points = chartInstance.value.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, false)
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
    const { ctx } = chart;
    chart.data.datasets.forEach((dataset, idx) => {
      if (dataset.label === 'Net') {
        const meta = chart.getDatasetMeta(idx);
        meta.data.forEach(bar => {
          const y = bar.y;
          const x = bar.x;
          // use configured barThickness for width
          const width = dataset.barThickness || 0;
          ctx.save();
          ctx.strokeStyle = getStyle('--color-accent-yellow');
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(x - width / 2, y);
          ctx.lineTo(x + width / 2, y);
          ctx.stroke();
          ctx.restore();
        });
      }
    });
  }
};

// Plugin to annotate above-average day counts when avg lines are shown
const avgInfoPlugin = {
  id: 'avgInfoPlugin',
  afterDraw(chart) {
    const { ctx, chartArea } = chart
    ctx.save()
    ctx.font = "12px 'Fira Code', monospace"
    ctx.textBaseline = 'top'
    let y = chartArea.top + 4
    if (showAvgIncome.value) {
      ctx.fillStyle = getStyle('--color-accent-green')
      ctx.fillText(`Income>avg: ${aboveAvgIncomeDays.value}`, chartArea.left + 4, y)
      y += 14
    }
    if (showAvgExpenses.value) {
      ctx.fillStyle = getStyle('--color-accent-red')
      ctx.fillText(`Expenses>avg: ${aboveAvgExpenseDays.value}`, chartArea.left + 4, y)
    }
    ctx.restore()
  }
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

  const labels = filtered.length ? filtered.map(item => item.date) : [' ']
  // Extract numeric values from response objects
  const netValues = filtered.length ? filtered.map(item => item.net.parsedValue) : [0]
  const incomeValues = filtered.length ? filtered.map(item => item.income.parsedValue) : [0]
  const expenseValues = filtered.length ? filtered.map(item => item.expenses.parsedValue) : [0]
  // Expenses are already negative (parsedValue); use as is for chart

  const avgIncome = incomeValues.length ? incomeValues.reduce((a, b) => a + b, 0) / incomeValues.length : 0
  const avgExpenses = expenseValues.length ? expenseValues.reduce((a, b) => a + b, 0) / expenseValues.length : 0

  const datasets = [
    {
      type: 'bar',
      label: 'Income',
      data: incomeValues,
      backgroundColor: getStyle('--color-accent-green'),
      borderRadius: 4,
      barThickness: 20,
    },
    {
      type: 'bar',
      label: 'Expenses',
      data: expenseValues,
      backgroundColor: getStyle('--color-accent-red'),
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
      data: movingAverage(netValues, 7),
      borderColor: getStyle('--color-accent-orange'),
      borderWidth: 2,
      pointRadius: 0,
    })
  }

  if (show30Day.value) {
    datasets.push({
      type: 'line',
      label: '30-Day Avg',
      data: movingAverage(netValues, 30),
      borderColor: getStyle('--color-accent-blue'),
      borderWidth: 2,
      pointRadius: 0,
    })
  }

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    // include netLinePlugin to draw net lines and avgInfoPlugin for annotations
    plugins: [netLinePlugin, avgInfoPlugin],
    data: {
      labels,
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 20, bottom: 20 } },
      plugins: {
        tooltip: {
          callbacks: {
            // Show the date as title
            title: (tooltipItems) => {
              const idx = tooltipItems[0].dataIndex;
              return filtered[idx]?.date || tooltipItems[0].label;
            },
            // Suppress default per-dataset labels
            label: () => null,
            // After title, display income, expenses, net, and transactions
            afterBody: (tooltipItems) => {
              const idx = tooltipItems[0].dataIndex;
              const rec = filtered[idx];
              if (!rec) return [];
              return [
                `Income: ${formatAmount(rec.income.parsedValue)}`,
                `Expenses: ${formatAmount(rec.expenses.parsedValue)}`,
                `Net: ${formatAmount(rec.net.parsedValue)}`,
                `Transactions: ${rec.transaction_count}`,
              ];
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
            callback: value => formatAmount(value),
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
              if (index % 7 !== 0) return '';
              // Use the original label (YYYY-MM-DD) for accurate parsing
              const raw = labels[index];
              if (!raw) return '';
              const dt = new Date(raw);
              if (isNaN(dt)) return raw;
              // Format e.g. "Jul 05"
              return dt.toLocaleDateString(undefined, { month: 'short', day: '2-digit' });
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
    const response = await fetchDailyNet()
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

  const days = filtered.length || 1
  const avgIncome = totalIncome / days
  const avgExpenses = totalExpenses / days
  aboveAvgIncomeDays.value = filtered.filter(d => (d.income?.parsedValue || 0) > avgIncome).length
  aboveAvgExpenseDays.value = filtered.filter(d => Math.abs(d.expenses?.parsedValue || 0) > Math.abs(avgExpenses)).length

  emit('summary-change', {
    totalIncome,
    totalExpenses,
    totalNet,
    aboveAvgIncomeDays: aboveAvgIncomeDays.value,
    aboveAvgExpenseDays: aboveAvgExpenseDays.value,
  })

  // Also emit the filtered chart data for the statistics component
  emit('data-change', filtered)
}


watch([chartData, () => props.zoomedOut, show7Day, show30Day, showAvgIncome, showAvgExpenses], async () => {
  updateSummary()
  await renderChart()
})

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

<style scoped>
.chart-controls {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.chart-controls label {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
</style>
