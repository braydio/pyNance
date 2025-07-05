
<template>
  <div class="chart-container card">
    <h2 class="heading-md">{{ chartTypeLabel }} Year Comparison</h2>
    <div class="toggle-group">
      <button
        v-for="type in chartTypes"
        :key="type.value"
        class="btn btn-pill"
        :class="{ active: activeChart === type.value }"
        @click="setChartType(type.value)"
      >
        {{ type.label }}
      </button>
    </div>
    <div class="chart-wrapper">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import api from '@/services/api.js'
import { ref, onMounted, nextTick } from 'vue'
import { Chart } from 'chart.js/auto'

const chartCanvas = ref(null)
const chartInstance = ref(null)
const chartData = ref([])
const activeChart = ref('assets')
const chartTypeLabel = ref('Assets')

const MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const currentYear = new Date().getFullYear()
const previousYear = currentYear - 1

const chartTypes = [
  { label: 'Assets', value: 'assets' },
  { label: 'Liabilities', value: 'liabilities' },
  { label: 'Net Worth', value: 'netWorth' }
]

function parseByType(year, key) {
  const result = new Array(12).fill(null)
  chartData.value.forEach(d => {
    const [y, m] = d.date.split('-').map(Number)
    if (y === year) result[m - 1] = d[key]
  })
  return result
}

function formatCurrency(val) {
  const num = Number(val || 0)
  return num < 0
    ? `($${Math.abs(num).toLocaleString()})`
    : `$${num.toLocaleString()}`
}

async function fetchData() {
  try {
    const data = await api.fetchNetAssets()
    chartData.value = Array.isArray(data?.data) ? data.data : []
    await nextTick()
    buildChart()
  } catch (e) {
    console.error('Chart fetch failed:', e)
  }
}

function buildChart() {
  if (!chartData.value.length) return
  if (chartInstance.value) chartInstance.value.destroy()

  const ctx = chartCanvas.value.getContext('2d')

  chartInstance.value = new Chart(ctx, {
    type: 'line',
    data: {
      labels: MONTH_LABELS,
      datasets: [
        {
          label: `${chartTypeLabel.value} (${previousYear})`,
          data: parseByType(previousYear, activeChart.value),
          borderColor: '#22d3ee',
          backgroundColor: 'rgba(137, 220, 235, 0.3)',
          fill: true,
          tension: 0.25
        },
        {
          label: `${chartTypeLabel.value} (${currentYear})`,
          data: parseByType(currentYear, activeChart.value),
          borderColor: '#fac15f',
          backgroundColor: 'rgba(250, 193, 95, 0.3)',
          fill: true,
          tension: 0.25
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#ddd',
            boxWidth: 14,
            usePointStyle: true
          }
        },
        tooltip: {
          backgroundColor: '#1e1e1e',
          borderColor: '#444',
          borderWidth: 1,
          callbacks: {
            label: ctx => `${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#aaa' },
          grid: { color: '#333' }
        },
        y: {
          ticks: {
            color: '#aaa',
            callback: formatCurrency
          },
          grid: { color: '#333' }
        }
      }
    }
  })
}

function setChartType(type) {
  activeChart.value = type
  chartTypeLabel.value = chartTypes.find(t => t.value === type).label
  buildChart()
}

onMounted(fetchData)
</script>

<style scoped>
@reference "../../assets/css/main.css";
.chart-container {
  width: 100%;
  padding: 0.75rem;
  background-color: var(--color-bg-secondary);
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow);
}

.toggle-group {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.toggle-group .btn.active {
  background: var(--color-accent-mint);
  color: var(--color-bg-dark);
  box-shadow: 0 0 6px var(--neon-mint);
}

.chart-wrapper {
  position: relative;
  height: 300px;
  width: 100%;
}

canvas {
  width: 100% !important;
  height: 100% !important;
}


</style>

