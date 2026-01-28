<!-- src/components/forecast/ForecastChart.vue -->
<template>
  <div class="chart-container">
    <div class="chart-header">
      <h2 class="chart-title">Forecast vs Actuals ({{ viewType }})</h2>
      <button @click="toggleView" class="toggle-button">
        Switch to {{ viewType === 'Month' ? 'Year' : 'Month' }}
      </button>
    </div>
    <div v-if="!hasData" class="chart-empty">Forecast chart data is not available yet.</div>
    <canvas v-else ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const props = defineProps({
  timeline: {
    type: Array,
    default: () => [],
  },
  viewType: String,
})

const emit = defineEmits(['update:viewType'])

const chartCanvas = ref(null)
let chartInstance = null

const labels = computed(() => props.timeline.map((point) => point.label))
const forecastLine = computed(() => props.timeline.map((point) => point.forecast_balance))
const actualLine = computed(() => props.timeline.map((point) => point.actual_balance))
const hasData = computed(() => labels.value.length > 0)

function toggleView() {
  emit('update:viewType', props.viewType === 'Month' ? 'Year' : 'Month')
}

/**
 * Tear down chart resources to avoid dangling canvas instances.
 */
function destroyChart() {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
}

/**
 * Render the forecast chart with latest timeline data.
 */
function renderChart() {
  if (!chartCanvas.value) return
  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return
  destroyChart()

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.value,
      datasets: [
        {
          label: 'Forecast',
          data: forecastLine.value,
          borderColor: '#3B82F6',
          tension: 0.3,
        },
        {
          label: 'Actual',
          data: actualLine.value,
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
onBeforeUnmount(destroyChart)
watch(() => [labels.value, forecastLine.value, actualLine.value], renderChart)
</script>

<style scoped>
@reference "../../assets/css/main.css";
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

.chart-empty {
  padding: 1.5rem;
  text-align: center;
  font-size: 0.9rem;
  color: var(--text-muted);
}
</style>
