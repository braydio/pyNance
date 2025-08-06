<template>
  <div class="daily-net-chart" style="height: 400px;">
    <canvas ref="chartCanvas" style="width: 100%; height: 100%;"></canvas>
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
// Emits "bar-click" when a bar is selected and "summary-change" when data totals change
const emit = defineEmits(['bar-click', 'summary-change'])

const chartInstance = ref(null)
const chartCanvas = ref(null)
const chartData = ref([])
const dateRange = ref('30') // default to 30 days

function getStyle(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
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

  const now = new Date()
  const rangeStart = new Date()
  if (!props.zoomedOut) {
    rangeStart.setMonth(rangeStart.getMonth() - 1)
  } else {
    rangeStart.setMonth(rangeStart.getMonth() - 6)
  }

  const filtered = (chartData.value || []).filter(item => {
    const d = new Date(item.date)
    return d >= rangeStart && d <= now
  })

  const labels = filtered.length ? filtered.map(item => item.date) : [' ']
  // Extract numeric values from response objects
  const netValues = filtered.length ? filtered.map(item => item.net.parsedValue) : [0]
  const incomeValues = filtered.length ? filtered.map(item => item.income.parsedValue) : [0]
  const expenseValues = filtered.length ? filtered.map(item => item.expenses.parsedValue) : [0]
  // Expenses are already negative (parsedValue); use as is for chart

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    // include netLinePlugin to draw net lines
    plugins: [netLinePlugin],
    data: {
      labels,
        datasets: [
          {
            type: 'bar',
            label: 'Income',
            data: incomeValues,
            backgroundColor: '#5db073',
            borderRadius: 4,
            barThickness: 20,
          },
          {
            type: 'bar',
            label: 'Expenses',
            data: expenseValues,
            backgroundColor: '#a43e5c',
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
        ],
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
                `🟢 Income: ${formatAmount(rec.income.parsedValue)}`,
                `🔴 Expenses: ${formatAmount(rec.expenses.parsedValue)}`,
                `🟡 Net: ${formatAmount(rec.net.parsedValue)}`,
                `📊 Transactions: ${rec.transaction_count}`,
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
  // Sum up parsed numeric values
  const totalIncome = (chartData.value || []).reduce(
    (sum, d) => sum + (d.income?.parsedValue || 0),
    0
  )
  const totalExpenses = (chartData.value || []).reduce(
    (sum, d) => sum + (d.expenses?.parsedValue || 0),
    0
  )
  const totalNet = (chartData.value || []).reduce(
    (sum, d) => sum + (d.net?.parsedValue || 0),
    0
  )
  emit('summary-change', { totalIncome, totalExpenses, totalNet })
}

function setRange(range) {
  dateRange.value = range
  fetchData()
}

watch([chartData, () => props.zoomedOut], async () => {
  await renderChart()
  updateSummary()
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
