<template>
  <div class="account-balance-history-chart" style="height:400px;">
    <canvas ref="chartCanvas" style="width:100%; height:100%;"></canvas>
  </div>
</template>

<script setup>
import { Chart } from 'chart.js/auto'
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { formatAmount } from '@/utils/format'

// Props: balances array with { date, balance }
const props = defineProps({
  balances: {
    type: Array,
    required: true
  }
})

const chartInstance = ref(null)
const chartCanvas = ref(null)

function renderChart() {
  if (chartInstance.value) {
    chartInstance.value.destroy()
    chartInstance.value = null
  }

  if (!props.balances || props.balances.length === 0) return

  const labels = props.balances.map(b => b.date)
  const values = props.balances.map(b => b.balance)

  const ctx = chartCanvas.value.getContext('2d')
  chartInstance.value = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Balance',
          data: values,
          borderColor: getStyle('--color-accent-green'),
          backgroundColor: 'transparent',
          fill: false,
          tension: 0.3,
          pointRadius: 0, // smooth line
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          enabled: true,
          backgroundColor: getStyle('--theme-bg'),
          borderColor: getStyle('--divider'),
          borderWidth: 1,
          callbacks: {
            label: (ctx) => `Balance: ${formatAmount(ctx.raw)}`
          }
        },
        legend: {
          display: true,
          labels: { color: getStyle('--color-text-muted') }
        }
      },
      scales: {
        y: {
          grid: { color: getStyle('--divider') },
          ticks: {
            callback: (value) => formatAmount(value),
            color: getStyle('--color-text-muted')
          }
        },
        x: {
          grid: { color: getStyle('--divider') },
          ticks: {
            maxRotation: 45,
            minRotation: 0,
            color: getStyle('--color-text-muted')
          }
        }
      }
    }
  })
}

onMounted(() => renderChart())
onUnmounted(() => {
  if (chartInstance.value) chartInstance.value.destroy()
})
watch(() => props.balances, renderChart, { deep: true })

function getStyle(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}
</script>
