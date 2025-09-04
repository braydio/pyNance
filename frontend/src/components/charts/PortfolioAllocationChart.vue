<template>
  <div class="chart-container">
    <h3 class="text-lg font-medium mb-2">Allocation by Type</h3>
    <div class="chart-wrap"><canvas ref="canvas"></canvas></div>
  </div>
</template>

<script setup>
import { Chart } from 'chart.js/auto'
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  allocations: { type: Array, required: true }, // [{ label, value }]
})

const canvas = ref(null)
let chart

function build() {
  if (!canvas.value) return
  if (chart) chart.destroy()
  const labels = props.allocations.map(a => a.label)
  const data = props.allocations.map(a => a.value)
  const colors = [
    '#22d3ee','#fac15f','#a78bfa','#34d399','#fca5a5','#f59e0b','#60a5fa','#4ade80','#f472b6'
  ]
  chart = new Chart(canvas.value.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data, backgroundColor: labels.map((_,i)=>colors[i%colors.length]) }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: '#ddd' } },
        tooltip: { callbacks: { label: ctx => `${ctx.label}: ${formatCurrency(ctx.parsed)}` } }
      }
    }
  })
}

function formatCurrency(n){
  const x = Number(n||0); return x.toLocaleString(undefined,{style:'currency',currency:'USD'})
}

onMounted(build)
onBeforeUnmount(()=>{ if (chart) chart.destroy() })
watch(()=>props.allocations, build, { deep: true })
</script>

<style scoped>
.chart-container { border: 1px solid var(--divider); border-radius: 8px; padding: .5rem .75rem; }
.chart-wrap { position: relative; height: 280px; }
</style>

