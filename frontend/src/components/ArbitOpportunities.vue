<template>
  <ul data-testid="opportunity-list">
    <li v-for="op in opportunities" :key="op.id">{{ op.symbol }} - {{ op.profit }}</li>
  </ul>
</template>

<script setup>
/**
 * Lists current arbitrage opportunities.
 */
import { ref, onMounted } from 'vue'
import { fetchArbitOpportunities } from '@/services/arbit'

const opportunities = ref([])

async function load() {
  const data = await fetchArbitOpportunities()
  opportunities.value = data.opportunities || []
}

onMounted(load)
</script>
