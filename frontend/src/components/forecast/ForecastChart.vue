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
import { ref, watch, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import { useForecastEngine } from '@/composables/useForecastEngine'

Chart.register(...registerables)

const props = defineProps({
  forecastItems: Array,
  viewType: String,
})

const emit = defineEmits(['update:viewType'])

const chartCanvas = ref(null)
let chartInstance = null

const recurringTxs = [
  { label: 'Net Salary', amount: 3000, frequency: 'monthly', nextDueDate: '2025-05-01' },
  { label: 'Subscription', amount: -30, frequency: 'monthly', nextDueDate: '2025-05-10' },
  { label: 'Car Loan', amount: -250, frequency: 'monthly', nextDueDate: '2025-05-12' }
]

const accountHistory = [
  { date: 'May 1', balance: 4200 },
  { date: 'May 2', balance: 4235 },
  { date: 'May 3', balance: 4190 },
  { date: 'May 4', balance: 4220 }
]

const engine = useForecastEngine(
  ref(props.viewType),
  recurringTxs,
  accountHistory,
  200, // manual income
  50   // liability rate
)

function toggleView() {
  emit('update:viewType', props.viewType === 'Month' ? 'Year' : 'Month')
}

function renderChart() {
  if (!chartCanvas.value) return
  const ctx = chartCanvas.value.getContext('2d')
  if (chartInstance) chartInstance.destroy()

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: engine.labels.value,
      datasets: [
        {
          label: 'Forecast',
          data: engine.forecastLine.value,
          borderColor: '#3B82F6',
          tension: 0.3,
        },
        {
          label: 'Actual',
          data: engine.actualLine.value,
          borderColor: '#10B981',
          tension: 0.3,
        },
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      scales: { y: { beginAtZero: false } }
    }
  })
}

onMounted(renderChart)

watch(
  () => [engine.labels.value, engine.forecastLine.value, engine.actualLine.value],
  renderChart
)
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
