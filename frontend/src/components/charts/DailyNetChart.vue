<template>
  <div class="daily-net-chart" style="height: 400px;">
    <canvas ref="chartCanvas" style="width: 100%; height: 100%;"></canvas>
  </div>
</template>

<script setup>
import { fetchDailyNet } from '@/api/charts'
import { fetchTransactions } from '@/api/transactions'
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Chart } from 'chart.js/auto'
import { formatAmount } from "@/utils/format"

const props = defineProps({ zoomedOut: { type: Boolean, default: false } })
const emit = defineEmits(['bar-click', 'summary-change', 'show-transactions'])

const chartInstance = ref(null)
const chartCanvas = ref(null)
const chartData = ref([])
const dateRange = ref('30') // default to 30 days

function getStyle(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

async function handleBarClick(evt) {
  if (!chartInstance.value) return
  const points = chartInstance.value.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, false)
  if (points.length) {
    const index = points[0].index
    const date = chartInstance.value.data.labels[index]
    emit('bar-click', date)
    try {
      const response = await fetchTransactions({ date })
      if (response.status === 'success') {
        emit('show-transactions', response.data)
      }
    } catch (error) {
      console.error('Error fetching transactions:', error)
    }
  }
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
  const netValues = filtered.length ? filtered.map(item => item.net) : [0]
  const incomeValues = filtered.length ? filtered.map(item => item.income) : [0]
  const expenseValues = filtered.length ? filtered.map(item => -item.expenses) : [0]

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
          backgroundColor: (getStyle('--color-accent-mint') || '#38ffd4') + '55',
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
      plugins: {
        tooltip: {
          callbacks: {
            label: (context) => `${context.dataset.label}: ${formatAmount(context.parsed.y)}`,
          },
          backgroundColor: getStyle('--theme-bg'),
          titleColor: getStyle('--color-accent-yellow'),
          bodyColor: getStyle('--color-text-light'),
          borderColor: getStyle('--color-accent-yellow'),
          borderWidth: 1,
        },
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
            maxTicksLimit: 14,
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
  const totalIncome = (chartData.value || []).reduce((sum, d) => sum + d.income, 0)
  const totalExpenses = (chartData.value || []).reduce((sum, d) => sum + d.expenses, 0)
  const totalNet = (chartData.value || []).reduce((sum, d) => sum + d.net, 0)
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
