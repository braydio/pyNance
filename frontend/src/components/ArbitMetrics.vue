<template>
  <div>
    <PortfolioAllocationChart v-if="profit.length" :allocations="profit" />
    <PortfolioAllocationChart v-if="latency.length" :allocations="latency" />
  </div>
</template>

<script setup lang="ts">
/**
 * Renders profit and latency metrics using existing chart components.
 */
import { ref, onMounted } from 'vue'
import { fetchArbitMetrics, type MetricPoint } from '@/services/arbit'
import PortfolioAllocationChart from '@/components/charts/PortfolioAllocationChart.vue'

const profit = ref<MetricPoint[]>([])
const latency = ref<MetricPoint[]>([])

async function load() {
  const data = await fetchArbitMetrics()
  profit.value = data.profit || []
  latency.value = data.latency || []
}

onMounted(load)
</script>
