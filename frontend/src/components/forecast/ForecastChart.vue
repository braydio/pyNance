<!-- src/components/forecast/ForecastChart.vue -->
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

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import { useForecastEngine } from '@/composables/useForecastEngine'

Chart.register(...registerables)

const props = defineProps<{
  forecastItems: any[]
  viewType: string
  manualIncome: number
  liabilityRate: number
  accountHistory: any[]
}>()

const emit = defineEmits(['update:viewType'])

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

const engine = useForecastEngine(
  ref(props.viewType),
  props.forecastItems,
  props.accountHistory,
  props.manualIncome,
  props.liabilityRate
)

function toggleView() {
  emit('update:viewType', props.viewType === 'Month' ? 'Year' : 'Month')
}

function renderChart() {
  if (!chartCanvas.value) return
  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return
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
      ],
    },
    options: {
      responsive: true,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      scales: {
        y: {
          beginAtZero: false,
        },
      },
    },
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
