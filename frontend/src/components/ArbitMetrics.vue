<template>
  <div>
    <PortfolioAllocationChart
      v-if="metrics.profit.length"
      :allocations="metrics.profit"
    />
    <PortfolioAllocationChart
      v-if="metrics.latency.length"
      :allocations="metrics.latency"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * Renders profit and latency metrics using existing chart components.
 */
import { reactive, onMounted } from 'vue'
import { fetchArbitMetrics, type ArbitMetricsResponse } from '@/services/arbit'
import PortfolioAllocationChart from '@/components/charts/PortfolioAllocationChart.vue'

const metrics = reactive<ArbitMetricsResponse>({ profit: [], latency: [] })

async function load() {
  const data = await fetchArbitMetrics()
  metrics.profit = data.profit ?? []
  metrics.latency = data.latency ?? []
}

onMounted(load)
</script>
