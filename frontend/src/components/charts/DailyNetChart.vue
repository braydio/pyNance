<template>
  <div
    class="daily-net-chart bg-[var(--color-bg-sec)] p-4 rounded-2xl shadow w-full border border-[var(--divider)] relative">
    <ChartWidgetTopBar>
      <template #icon>
        <!-- Mint/green dollar sign as visual cue -->
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-[var(--color-accent-mint)]" fill="none"
          viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 8c-2.21 0-4-1.343-4-3s1.79-3 4-3 4 1.343 4 3c0 1.216-1.024 2.207-2.342 2.707M12 12c2.21 0 4 1.343 4 3s-1.79 3-4 3-4-1.343-4-3c0-1.216 1.024-2.207 2.342-2.707" />
        </svg>
      </template>
      <template #title>
        Daily Net Income
      </template>
      <template #controls>
        <button
          class="bg-[var(--color-accent-yellow)] text-[var(--color-text-dark)] px-3 py-1 rounded font-semibold transition hover:brightness-105"
          @click="toggleZoom">
          {{ zoomedOut ? 'Zoom In' : 'Zoom Out' }}
        </button>
      </template>
      <template #summary>
        <div>Income: <span class="font-bold text-[var(--color-accent-mint)]">${{ summary.totalIncome.toLocaleString()
        }}</span></div>
        <div>Expenses: <span class="font-bold text-[var(--color-accent-red)]">${{ summary.totalExpenses.toLocaleString()
        }}</span></div>
        <div class="font-bold text-lg text-[var(--color-accent-mint)]">Net Total: ${{ summary.totalNet.toLocaleString()
        }}</div>
      </template>
    </ChartWidgetTopBar>

    <div
      class="relative w-full h-[400px] bg-[var(--theme-bg)] rounded-xl overflow-hidden border border-[var(--divider)]">
      <canvas ref="chartCanvas" class="absolute inset-0 w-full h-full"></canvas>
    </div>
  </div>
</template>

<script setup>
/**
 * DailyNetChart - unified style widget for net income per day.
 * Now uses ChartWidgetTopBar for visual/structural consistency.
 */
import { fetchDailyNet } from '@/api/charts'
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
import { Chart } from 'chart.js/auto'
import ChartWidgetTopBar from '@/components/ui/ChartWidgetTopBar.vue'

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

function getStyle(name) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim()
}

function renderChart() {
  const canvasEl = chartCanvas.value
  if (!canvasEl) return
  const ctx = canvasEl.getContext('2d')
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
@import "../../assets/css/main.css";

.daily-net-chart .relative {
  background: var(--theme-bg);
  border-radius: 1rem;
  box-shadow: 0 1px 8px 0 rgb(30 41 59 / 10%);
}
</style>
