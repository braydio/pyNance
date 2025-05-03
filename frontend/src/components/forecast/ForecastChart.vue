<template>
  <div class="chart-container">
    <div class="chart-header">
      <h2 class="chart-title">Forecast vs Actuals ({{ viewType }})</h2>
      <button @click="toggleView" class="toggle-button">
        Switch to {{ viewType === 'Month' ? 'Year' : 'Month' }}
      </button>
    </div>
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const props = defineProps({
  forecastItems: {
    type: Array,
    default: () => [],
  },
  viewType: {
    type: String,
    default: 'Month',
  },
})

const emit = defineEmits(['update:viewType'])

const chartCanvas = ref(null)
let chartInstance = null

function toggleView() {
  emit('update:viewType', props.viewType === 'Month' ? 'Year' : 'Month')
}

function getMonthDates() {
  const today = new Date()
  const year = today.getFullYear()
  const month = today.getMonth()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  return Array.from({ length: daysInMonth }, (_, i) =>
    new Date(year, month, i + 1).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
  )
}

function getYearMonths() {
  return Array.from({ length: 12 }, (_, i) =>
    new Date(new Date().getFullYear(), i, 1).toLocaleDateString(undefined, { month: 'short' })
  )
}

const labels = computed(() => props.viewType === 'Month' ? getMonthDates() : getYearMonths())

const forecastData = computed(() =>
  labels.value.map((_, i) => props.viewType === 'Month' ? 4000 + i * 20 : 5000 + i * 300)
)
const actualData = computed(() =>
  labels.value.map((_, i) => props.viewType === 'Month' ? 3900 + i * 18 : 4800 + i * 280)
)

function renderChart() {
  if (!chartCanvas.value) return
  const ctx = chartCanvas.value.getContext('2d')
  if (chartInstance) chartInstance.destroy()

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.value,
      datasets: [
        {
          label: 'Forecast',
          data: forecastData.value,
          borderColor: '#3B82F6',
          tension: 0.3,
        },
        {
          label: 'Actual',
          data: actualData.value,
          borderColor: '#10B981',
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      scales: { y: { beginAtZero: false } },
    },
  })
}

onMounted(renderChart)
watch(() => [labels.value, forecastData.value, actualData.value], renderChart)
</script>

<style scoped>
.chart-container {
  background-color: var(--surface);
  color: var(--theme-fg);
  border: 1px solid var(--divider);
  border-radius: 0.5rem;
  padding: 1rem;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.chart-title {
  font-size: 1.125rem;
  font-weight: 600;
}

.toggle-button {
  font-size: 0.875rem;
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--divider);
  border-radius: 0.375rem;
  background-color: var(--input-bg);
  color: var(--theme-fg);
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.toggle-button:hover {
  background-color: var(--hover-bg);
}
</style>
