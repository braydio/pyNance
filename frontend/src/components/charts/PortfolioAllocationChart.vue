<template>
  <div class="chart-container">
    <h3 class="text-lg font-medium mb-2">Allocation by Type</h3>
    <div class="chart-wrap"><canvas ref="canvas"></canvas></div>
  </div>
</template>

<script setup>
import { Chart } from 'chart.js/auto'
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { getAccentColor } from '@/utils/colors'

const props = defineProps({
  allocations: { type: Array, required: true }, // [{ label, value }]
})

const canvas = ref(null)
let chart

function build() {
  if (!canvas.value) return
  if (chart) chart.destroy()
  const labels = props.allocations.map((a) => a.label)
  const data = props.allocations.map((a) => a.value)
  const colors = labels.map((_, i) => getAccentColor(i))
  chart = new Chart(canvas.value.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data, backgroundColor: colors }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: true, labels: { color: getStyle('--color-text-muted') } },
        tooltip: {
          enabled: true,
          backgroundColor: getStyle('--theme-bg'),
          borderColor: getStyle('--divider'),
          borderWidth: 1,
          callbacks: { label: (ctx) => `${ctx.label}: ${formatCurrency(ctx.parsed)}` },
        },
      },
    },
  })
}

function formatCurrency(n) {
  const x = Number(n || 0)
  return x.toLocaleString(undefined, { style: 'currency', currency: 'USD' })
}

onMounted(build)
onBeforeUnmount(() => {
  if (chart) chart.destroy()
})
watch(() => props.allocations, build, { deep: true })

function getStyle(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}
</script>

<style scoped>
.chart-container {
  border: 1px solid var(--divider);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
}
.chart-wrap {
  position: relative;
  height: 280px;
}
</style>
