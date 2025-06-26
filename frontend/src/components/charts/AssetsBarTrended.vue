<template>
  <div class="chart-container card">
    <h2 class="heading-md">Net Assets Trend</h2>
    <div class="chart-wrapper">
      <canvas ref="canvasRef"></canvas>
    </div>
  </div>
</template>

<script setup>
import api from '@/services/api'
import { Chart } from 'chart.js/auto'
import { onMounted, ref, nextTick } from 'vue'

const canvasRef = ref()
const chartInstance = ref(null)
const chartData = ref([])

const format = val => {
  const n = Number(val || 0)
  return n < 0
    ? `($${Math.abs(n).toLocaleString()})`
    : `$${n.toLocaleString()}`
}

const parseDate = str =>
  new Date(str).toLocaleDateString('default', {
    month: 'short',
    day: 'numeric'
  })

async function fetchData() {
  try {
    const data = await api.fetchNetAssets()
    chartData.value = Array.isArray(data?.data) ? data.data : []
    await nextTick()
    render()
  } catch (e) {
    console.error('Chart fetch error:', e)
  }
}

function render() {
  if (!chartData.value.length) return
  if (chartInstance.value) chartInstance.value.destroy()

  const ctx = canvasRef.value.getContext('2d')

  chartInstance.value = new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartData.value.map(d => parseDate(d.date)),
      datasets: [
        {
          label: 'Assets',
          data: chartData.value.map(d => d.assets),
          borderColor: '#00ffa5',
          backgroundColor: '#98e8ff',
          tension: 0.2,
          fill: true
        },
        {
          label: 'Liabilities',
          data: chartData.value.map(d => d.liabilities),
          borderColor: '#ff6a6a',
          backgroundColor: '#ffc0cb',
          tension: 0.2,
          fill: true
        }
      ]
    },
    options: {
      animation: { duration: 900, easing: 'easeOutCubic' },
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          backgroundColor: '#1f1f1f',
          borderColor: '#444',
          borderWidth: 1,
          callbacks: {
            label: ctx => `${ctx.dataset.label}: ${format(ctx.raw)}`
          }
        },
        legend: {
          labels: {
            color: '#ccc',
            boxWidth: 16,
            usePointStyle: true
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#aaa' },
          grid: { color: '#333' }
        },
        y: {
          ticks: {
            color: '#aaa',
            callback: format
          },
          grid: { color: '#333' }
        }
      }
    }
  })
}

onMounted(fetchData)
</script>

<style scoped>
@reference "../../assets/css/main.css";
.chart-container {
  width: 100%;
  padding: 0.75rem;
  background-color: var(--color-bg-secondary);
  border-radius: 12px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.15);
  transition: box-shadow 0.3s;
}

.chart-container:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

.chart-wrapper {
  position: relative;
  height: 300px;
  width: 100%;
}

canvas {
  width: 100% !important;
  height: 100% !important;
}


</style>
