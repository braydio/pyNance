<template>
  <div
    class="daily-net-chart bg-[var(--color-bg-sec)] p-4 rounded-2xl shadow w-full border border-[var(--divider)] relative">
    <div class="flex justify-between items-center mb-2">
      <h2 class="text-xl font-semibold">Daily Net Income</h2>
      <button class="bg-[var(--color-accent-yellow)] text-[var(--color-text-dark)] px-3 py-1 rounded font-semibold"
        @click="toggleZoom">
        {{ zoomedOut ? 'Zoom In' : 'Zoom Out' }}
      </button>
    </div>
    <div
      class="chart-summary absolute top-2 right-2 bg-[var(--color-bg-secondary)] px-3 py-2 rounded font-mono text-[var(--color-text-muted)] z-10 text-right border-2 border-[var(--divider)] shadow backdrop-blur-sm transition">
      <div class="summary-line income">Income: ${{ summary.totalIncome.toLocaleString() }}</div>
      <div class="summary-line expenses">Expenses: ${{ summary.totalExpenses.toLocaleString() }}</div>
      <div class="summary-line net font-bold text-lg text-[var(--color-accent-mint)]">Net Total: ${{
        summary.totalNet.toLocaleString() }}</div>
    </div>
    <div class="relative w-full h-[400px]">
      <canvas ref="chartCanvas" class="absolute inset-0 w-full h-full"></canvas>
    </div>
  </div>
</template>

<script setup>
/**
 * DailyNetChart displays daily income and expenses with a net line.
 * Emits a `bar-click` event when a bar is clicked.
 */
import { fetchDailyNet } from '@/api/charts'
import { ref, onMounted, onUnmounted, nextTick, computed, watch, defineEmits } from 'vue'
import { Chart } from 'chart.js/auto'

const emit = defineEmits(['bar-click'])

const chartInstance = ref(null)
const chartCanvas = ref(null)
const chartData = ref([])
const zoomedOut = ref(false)

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

function toggleZoom() {
  zoomedOut.value = !zoomedOut.value
}

// Emit selected date when a bar is clicked
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

watch([chartData, zoomedOut], async () => {
  await nextTick()
  renderChart()
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

function renderChart() {
  const canvasEl = chartCanvas.value
  if (!canvasEl) return
  const ctx = canvasEl.getContext('2d')
  if (!ctx) return

  if (chartInstance.value) {
    chartInstance.value.destroy()
    chartInstance.value = null
  }

  const now = new Date()
  const rangeStart = new Date()
  if (!zoomedOut.value) {
    rangeStart.setMonth(rangeStart.getMonth() - 1)
  } else {
    rangeStart.setMonth(rangeStart.getMonth() - 6)
  }

  const filtered = (chartData.value || []).filter(item => {
    const d = new Date(item.date)
    return d >= rangeStart && d <= now
  })

  const labels = filtered.map(item => item.date)
  const netValues = filtered.map(item => item.net)
  const incomeValues = filtered.map(item => item.income)
  const expenseValues = filtered.map(item => item.expenses)

  const getStyle = name =>
    getComputedStyle(document.documentElement).getPropertyValue(name).trim()

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
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
        {
          type: 'line',
          label: 'Net',
          data: netValues,
          borderColor: getStyle('--color-accent-mint') || '#38ffd4',
          backgroundColor: getStyle('--color-accent-mint') || '#38ffd4',
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 20, bottom: 20 } },
      scales: {
        x: {
          stacked: true,
          ticks: {
            maxTicksLimit: 14,
            color: getStyle('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 14 },
          },
          grid: { color: getStyle('--divider') },
        },
        y: {
          beginAtZero: true,
          ticks: {
            callback: value => `$${value}`,
            color: getStyle('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 14 },
          },
          grid: { color: getStyle('--divider') },
        },
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: context => {
              const index = context.dataIndex
              const dataPoint = filtered[index]
              return [
                `Net: $${dataPoint.net.toLocaleString()}`,
                `Income: $${dataPoint.income.toLocaleString()}`,
                `Expenses: $${dataPoint.expenses.toLocaleString()}`,
                `Transactions: ${dataPoint.transaction_count}`,
              ]
            },
          },
          backgroundColor: getStyle('--themed-bg'),
          titleColor: getStyle('--color-accent-yellow'),
          bodyColor: getStyle('--color-text-light'),
          borderColor: getStyle('--color-accent-yellow'),
          borderWidth: 1,
        },
        legend: { display: false },
      },
      onClick: handleBarClick,
    },
  })
}

const summary = computed(() => {
  const totalIncome = (chartData.value || []).reduce((sum, d) => sum + d.income, 0)
  const totalExpenses = (chartData.value || []).reduce((sum, d) => sum + d.expenses, 0)
  const totalNet = (chartData.value || []).reduce((sum, d) => sum + d.net, 0)
  return { totalIncome, totalExpenses, totalNet }
})
</script>

<style scoped>
@reference "../../assets/css/main.css";
/* Only theme stuff, NO height, width, min-width, min-height here */
.chart-summary .summary-line.net {
  text-shadow: 0 0 4px var(--neon-mint);
}
</style>
