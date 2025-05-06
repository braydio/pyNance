<template>
  <div class="chart-container card">
    <h2 class="heading-md">Net Assets Trend</h2>
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup>
import axios from 'axios'
import { Chart } from 'chart.js/auto'
import { onMounted, ref } from 'vue'

const canvasRef = ref()
const chartInstance = ref()
const chartData = ref([])

const format = (val) => {
  const n = Number(val || 0)
  return n < 0 ? `($${Math.abs(n).toLocaleString()})` : `$${n.toLocaleString()}`
}

const parseDate = (str) => new Date(str).toLocaleString('default', { month: 'short', day: 'numeric' })

async function fetchData() {
  try {
    const { data } = await axios.get('/api/charts/net_assets')
    chartData.value = data?.data || []
    render()
  } catch (e) {
    console.error('fetch error:', e)
  }
}

function render() {
  if (chartInstance.value) chartInstance.value.destroy()
  const ctx = canvasRef.value.getContext('2d')

  const fillA = ctx.createLinearGradient(0, 0, 0, 300)
  fillA.addColorStop(0, 'rgba(0, 255, 135, 0.2)')
  fillA.addColorStop(1, 'rgba(0, 255, 135, 0)')

  const fillL = ctx.createLinearGradient(0, 0, 0, 300)
  fillL.addColorStop(0, 'rgba(255, 87, 87, 0.3)')
  fillL.addColorStop(1, 'rgba(255, 87, 87, 0)')

  chartInstance.value = new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartData.value.map(d => parseDate(d.date)),
      datasets: [
        {
          label: 'Assets',
          data: chartData.value.map(d => d.assets),
          borderColor: '#00ffaa',
          backgroundColor: fillA,
          tension: 0.2,
          fill: true
        },
        {
          label: 'Liabilities',
          data: chartData.value.map(d => d.liabilities),
          borderColor: '#ff5757',
          backgroundColor: fillL,
          tension: 0.2,
          fill: true
        }
      ]
    },
    options: {
      animation: {
        duration: 800,
        easing: 'easeOutQuart'
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: ctx => `${ctx.dataset.label}: ${format(ctx.raw)}`
          }
        },
        legend: {
          labels: {
            color: '#ccc'
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#888' },
          grid: { color: '#333' }
        },
        y: {
          ticks: {
            color: '#888',
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
