<template>
  <div class="category-breakdown-chart">
    <div class="header-row">
      <h2 class="text-xl font-semibold mb-2">Spending by Category</h2>
      <input type="date" v-model="startDate" class="date-picker" />
      <input type="date" v-model="endDate" class="date-picker" />
      <div class="chart-summary">
        <span>Total Spending: {{ totalSpending.toLocaleString() }}</span>
      </div>
    </div>
    <div class="legend" v-if="availableCategories.length">
      <label
        v-for="cat in availableCategories"
        :key="cat"
        class="legend-item"
      >
        <input type="checkbox" v-model="selectedCategories" :value="cat" />
        <span>{{ cat }}</span>
      </label>
    </div>
    <div class="canvas-wrapper">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { Chart } from 'chart.js/auto'
import api from '@/services/api'

const emit = defineEmits(['bar-click'])

const chartCanvas = ref(null)
const chartInstance = ref(null)
const chartData = ref({ labels: [], amounts: [], raw: [] })
const selectedCategories = ref([])
const availableCategories = computed(() =>
  chartData.value.raw.map((e) => e.category || 'Uncategorized'),
)

const endDate = ref(new Date().toISOString().slice(0, 10))
const startDate = ref(
  new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().slice(0, 10),
)

const totalSpending = computed(() => {
  return chartData.value.amounts.reduce((sum, val) => sum + val, 0)
})

watch([startDate, endDate], () => fetchData())
watch(selectedCategories, () => updateChart())

async function fetchData() {
  try {
    const response = await api.fetchCategoryBreakdown({
      start_date: startDate.value,
      end_date: endDate.value,
    })

    if (response.status === 'success') {
      chartData.value.raw = (response.data || []).filter((entry) => {
        const isValid = entry && typeof entry.amount === 'number' && !isNaN(entry.amount)
        if (!isValid) console.warn('Skipping invalid entry:', entry)
        return isValid
      })
      await nextTick()
      selectedCategories.value = availableCategories.value.slice()
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

  const filtered = chartData.value.raw
    .filter((e) => selectedCategories.value.includes(e.category || 'Uncategorized'))
    .sort((a, b) => b.amount - a.amount)

  const labels = filtered.map((e) => e.category || 'Uncategorized')
  const data = filtered.map((e) => Math.round(Number(e.amount) || 0))

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
  @apply text-xl font-semibold mb-2 mt-0 text-neon-purple;
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

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: var(--color-text-light);
}
</style>
