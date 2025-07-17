<template>
  <div class="relative w-full h-[400px] bg-[var(--theme-bg)] rounded-xl overflow-hidden border border-[var(--divider)]">
    <canvas ref="chartCanvas" class="absolute inset-0 w-full h-full"></canvas>
  </div>
</template>

<script setup>
import { fetchDailyNet } from '@/api/charts'
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
import { Chart } from 'chart.js/auto'

const props = defineProps({
  zoomedOut: { type: Boolean, default: false }
})

const emit = defineEmits(['bar-click', 'summary-change'])

const chartInstance = ref(null)
const chartCanvas = ref(null)
const chartData = ref([])

function getStyle(name) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim()
}

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

async function renderChart() {
  await nextTick();
  const canvasEl = chartCanvas.value;
  if (!canvasEl) {
    console.warn('Chart canvas not ready!');
    return;
  }
  const ctx = canvasEl.getContext('2d');
  if (!ctx) {
    console.warn('Chart context not available!');
    return;
  }

  if (chartInstance.value) {
    chartInstance.value.destroy();
    chartInstance.value = null;
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
  const expenseValues = filtered.length ? filtered.map(item => item.expenses) : [0]

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
            label: (context) => {
              return `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`
            },
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
        y: {
          display: true,
          beginAtZero: true,
          grid: { display: true, color: getStyle('--divider') },
          ticks: {
            callback: value => value < 0
              ? `($${Math.abs(value).toLocaleString()})`
              : `$${value.toLocaleString()}`,
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
      // Summary and chart will update through the watch handler
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

<style scoped>
@reference "../../assets/css/main.css";

.relative {
  background: var(--theme-bg);
  border-radius: 1rem;
  box-shadow: 0 1px 8px 0 rgb(30 41 59 / 10%);
}
</style>
