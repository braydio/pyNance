// /frontend/src/components/forecast/ForecastChart.vue
<template>
  <div class="border rounded-2xl p-4 bg-white shadow">
    <h2 class="text-xl font-semibold mb-4">Projected Balance Trend</h2>
    <div class="h-64">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup>
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement)

const props = defineProps({
  forecastItems: Array
})

// ===== MOCK DATA LOADER =====
const base = 4300
const dailyDelta = props.forecastItems.reduce((sum, item) => sum + item.amount, 0) / 30

// Simulate small fluctuations for realism
const balanceData = Array.from({ length: 30 }, (_, i) =>
  (base + i * dailyDelta + (Math.random() * 50 - 25)).toFixed(2)
)

const chartData = {
  labels: Array.from({ length: 30 }, (_, i) => `Day ${i + 1}`),
  datasets: [
    {
      label: 'Projected Balance',
      data: balanceData,
      fill: true,
      tension: 0.3,
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      pointRadius: 2
    }
  ]
}

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top'
    },
    title: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: false,
      ticks: {
        callback: value => `$${value}`
      }
    }
  }
}
</script>

<style scoped>
canvas {
  max-height: 250px;
}
</style>
