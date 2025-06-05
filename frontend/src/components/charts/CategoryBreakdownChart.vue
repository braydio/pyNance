<template>
  <div class="category-breakdown-chart">
    <div class="header-row">
      <h2>Spending by Category</h2>
      <input type="date" v-model="startDate" class="date-picker" />
      <input type="date" v-model="endDate" class="date-picker" />
      <div class="chart-summary">
        <span>Total Spending: {{ totalSpending.toLocaleString() }}</span>
      </div>
    </div>
    <div class="canvas-wrapper">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { Chart } from 'chart.js/auto'
import axios from 'axios'

const emit = defineEmits(['bar-click'])

const chartCanvas = ref(null)
const chartInstance = ref(null)
const chartData = ref({ labels: [], amounts: [], raw: [] })

const endDate = ref(new Date().toISOString().slice(0, 10))
const startDate = ref(
  new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().slice(0, 10),
)

const totalSpending = computed(() => {
  return chartData.value.amounts.reduce((sum, val) => sum + val, 0)
})

watch([startDate, endDate], () => fetchData())

async function fetchData() {
  try {
    const response = await axios.get('/api/charts/category_breakdown', {
      params: { start_date: startDate.value, end_date: endDate.value },
    })

    if (response.data.status === 'success') {
      chartData.value.raw = (response.data.data || []).filter((entry) => {
        const isValid = entry && typeof entry.amount === 'number' && !isNaN(entry.amount)
        if (!isValid) console.warn('Skipping invalid entry:', entry)
        return isValid
      })
      updateChart()
    }
  } catch (err) {
    console.error('Error fetching category breakdown data:', err)
  }
}

function updateChart() {
  const canvasEl = chartCanvas.value
  if (!canvasEl) return
  const ctx = canvasEl.getContext('2d')
  if (!ctx) return
  if (chartInstance.value) chartInstance.value.destroy()

  const sorted = [...chartData.value.raw].sort((a, b) => b.amount - a.amount)
  const topN = 5
  const top = sorted.slice(0, topN)
  const others = sorted.slice(topN)

  const labels = top.map((e) => e.category || 'Uncategorized')
  const data = top.map((e) => Math.round(Number(e.amount) || 0))

  if (others.length > 0) {
    const otherTotal = others.reduce((sum, entry) => sum + (Number(entry.amount) || 0), 0)
    if (otherTotal > 0) {
      labels.push('Other')
      data.push(Math.round(otherTotal))
    }
  }

  chartData.value.labels = labels
  chartData.value.amounts = data

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Spending',
          data,
          backgroundColor: '#a78bfa',
          borderColor: '#7c3aed',
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => `$${context.raw.toLocaleString()}`,
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: '#c4b5fd',
            font: { size: 12 },
          },
        },
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => `$${value}`,
            color: '#c4b5fd',
            font: { size: 12 },
          },
        },
      },
      onClick: (evt) => {
        const points = chartInstance.value.getElementsAtEventForMode(
          evt,
          'nearest',
          { intersect: true },
          true,
        )
        if (points.length) {
          const index = points[0].index
          const label = chartData.value.labels[index]
          emit('bar-click', label)
        }
      },
    },
  })
}

onMounted(fetchData)
</script>

<style scoped>
.category-breakdown-chart {
  margin: 1rem;
  background-color: var(--color-bg-sec);
  padding: 1rem;
  border-radius: 12px;
  box-shadow:
    0 4px 16px var(--shadow),
    0 0 6px var(--hover-glow);
  position: relative;
  height: 400px;
  min-width: 300px;
  width: 100%;
  border: 1px solid var(--divider);
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.header-row h2 {
  margin: 0;
  color: var(--neon-purple);
}

.chart-summary {
  background: var(--color-bg-secondary);
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-family: 'SourceCodeVF', monospace;
  color: var(--color-text-muted);
  box-shadow: 0 2px 8px var(--shadow);
  border: 2px solid var(--divider);
}

.canvas-wrapper {
  height: 100%;
  background: var(--themed-bg);
  border-radius: 1rem;
}

.date-picker {
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  background-color: var(--themed-bg);
  border: 1px solid var(--divider);
  color: var(--color-text-light);
}
</style>
