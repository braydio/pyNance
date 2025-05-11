<template>
  <div class="chart-container card">
    <h2 class="heading-md">Net Assets Trend</h2>
    <canvas ref="canvasRef"></canvas>
  </div>
</template>


<script setup>
import axios from 'axios'
import { Chart } from 'chart.js/auto'
import { onMounted, ref, nextTick } from 'vue'

const canvasRef = ref()
const chartInstance = ref(null)
const chartData = ref([])

const format = (val) => {
  const n = Number(val || 0)
  return n < 0
    ? `($${Math.abs(n).toLocaleString()})`
    : `$${n.toLocaleString()}`
}

const parseDate = (str) =>
  new Date(str).toLocaleDateString('default', {
    month: 'short',
    day: 'numeric',
  })

async function fetchData() {
  try {
    const { data } = await axios.get('/api/charts/net_assets')
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
          fill: true,
        },
        {
          label: 'Liabilities',
          data: chartData.value.map(d => d.liabilities),
          borderColor: '#ff6a6a',
          backgroundColor: '#ffc0cb',
          tension: 0.2,
          fill: true,
        }
      ]
    },
    options: {
      animation: { duration: 900, easing: 'easeOutCubic' },
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
            usePointStyle: true,
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
.chart-container {
  padding: 1.5rem;
  background-color: var(--color-bg-secondary);
  border-radius: 12px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.15);
  transition: box-shadow 0.3s;
}

.chart-container:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}
</style>
