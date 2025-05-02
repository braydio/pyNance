<template>
  <div class="bg-white rounded-2xl shadow p-6 space-y-4">
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-semibold">Forecast vs Realized</h2>
      <button class="text-sm px-3 py-1 border rounded hover:bg-gray-100" @click="emitToggleView">
        View: {{ viewType }}
      </button>
    </div>
    <div class="h-64">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, Title, Tooltip, Legend,
  LineElement, CategoryScale, LinearScale, PointElement
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement)

const props = defineProps({
  forecastItems: Array,
  viewType: String
})
const emit = defineEmits(['update:viewType'])

function emitToggleView() {
  emit('update:viewType', props.viewType === 'Month' ? 'Year' : 'Month')
}

function generateLabels(view) {
  return view === 'Year'
    ? Array.from({ length: 12 }, (_, i) =>
      new Date(0, i).toLocaleString('default', { month: 'short' })
    )
    : Array.from({ length: 31 }, (_, i) => `Day ${i + 1}`) // Fixed 31 for simplicity
}

const chartData = computed(() => {
  const labels = generateLabels(props.viewType)
  const len = labels.length
  const forecast = Array.from({ length: len }, (_, i) =>
    (4400 + i * 15 + Math.random() * 80 - 40).toFixed(2)
  )
  const realized = forecast.map(val =>
    (parseFloat(val) - 100 + Math.random() * 50 - 25).toFixed(2)
  )

  return {
    labels,
    datasets: [
      {
        label: 'Forecast',
        data: forecast,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Realized',
        data: realized,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.05)',
        fill: true,
        tension: 0.4
      }
    ]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'top' } },
  scales: {
    y: { ticks: { callback: val => `$${val}` } }
  }
}
</script>

<style scoped>
canvas {
  max-height: 250px;
}
</style>
