<template>
  <div data-testid="arbit-status">
    <div v-if="loading">Loading...</div>
    <div v-else>Engine is {{ status.running ? 'running' : 'stopped' }}</div>
  </div>
</template>

<script setup>
/**
 * Displays the current arbitrage engine status.
 */
import { ref, onMounted } from 'vue'
import { fetchArbitStatus } from '@/services/arbit'

const status = ref({ running: false })
const loading = ref(true)

async function load() {
  try {
    status.value = await fetchArbitStatus()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
