<template>
  <div>
    <PortfolioAllocationChart v-if="profit.length" :allocations="profit" />
    <PortfolioAllocationChart v-if="latency.length" :allocations="latency" />
  </div>
</template>

<script setup>
/**
 * Renders profit and latency metrics using existing chart components.
 */
import { ref, onMounted } from 'vue'
import { fetchArbitMetrics } from '@/services/arbit'
import PortfolioAllocationChart from '@/components/charts/PortfolioAllocationChart.vue'

const profit = ref([])
const latency = ref([])

async function load() {
  const data = await fetchArbitMetrics()
  profit.value = data.profit || []
  latency.value = data.latency || []
}

onMounted(load)
</script>
