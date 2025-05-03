<template>
  <div class="chart-container">
    <h2>Forecast Chart ({{ viewType }})</h2>
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { onMounted, watch, ref } from 'vue'
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

let chartInstance
const chartCanvas = ref(null)

function renderChart() {
  if (!chartCanvas.value) return

  const ctx = chartCanvas.value.getContext('2d')
  if (chartInstance) chartInstance.destroy()

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
      datasets: [
        {
          label: 'Forecast',
          data: [1000, 2000, 3000, 4000],
          borderColor: 'blue',
          fill: false,
        },
        {
          label: 'Actual',
          data: [800, 1900, 2900, 3900],
          borderColor: 'green',
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
    },
  })
}

onMounted(() => {
  renderChart()
})

watch(() => [props.forecastItems, props.viewType], () => {
  renderChart()
})
</script>

<style scoped>
.chart-container {
  padding: 1rem;
  border: 1px solid #ccc;
}
</style>
