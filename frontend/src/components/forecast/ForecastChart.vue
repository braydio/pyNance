<template>
  <div class="chart-container">
    <div class="flex justify-between items-center mb-2">
      <h2 class="text-lg font-semibold">Forecast vs Actuals ({{ viewType }})</h2>
      <button @click="toggleView" class="text-sm border px-3 py-1 rounded hover:bg-gray-100">
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

// --- 🧠 Date series generator ---
function getMonthDates() {
  const today = new Date()
  const year = today.getFullYear()
  const month = today.getMonth()
  const daysInMonth = new Date(year, month + 1, 0).getDate()

  return Array.from({ length: daysInMonth }, (_, i) => {
    const day = new Date(year, month, i + 1)
    return day.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
  })
}

function getYearMonths() {
  return Array.from({ length: 12 }, (_, i) => {
    const date = new Date(new Date().getFullYear(), i, 1)
    return date.toLocaleDateString(undefined, { month: 'short' })
  })
}

const labels = computed(() => {
  return props.viewType === 'Month' ? getMonthDates() : getYearMonths()
})

const forecastData = computed(() => {
  return labels.value.map((_, i) => {
    return props.viewType === 'Month'
      ? 4000 + i * 20 // mock linear growth
      : 5000 + i * 300
  })
})

const actualData = computed(() => {
  return labels.value.map((_, i) => {
    return props.viewType === 'Month'
      ? 3900 + i * 18 // slightly behind forecast
      : 4800 + i * 280
  })
})

// --- 📈 Chart render ---
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
          borderColor: '#3B82F6', // Tailwind blue-500
          tension: 0.3,
        },
        {
          label: 'Actual',
          data: actualData.value,
          borderColor: '#10B981', // Tailwind green-500
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

onMounted(() => {
  renderChart()
})

watch(() => [labels.value, forecastData.value, actualData.value], () => {
  renderChart()
})
</script>

<style scoped>
.chart-container {
  padding: 1rem;
  border: 1px solid #ccc;
  background: white;
  border-radius: 0.5rem;
}
</style>
