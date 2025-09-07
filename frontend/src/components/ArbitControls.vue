<template>
  <div>
    <button class="start-btn" @click="start">Start</button>
    <button class="stop-btn" @click="stop">Stop</button>
    <div>Status: {{ status.running ? 'running' : 'stopped' }}</div>
  </div>
</template>

<script setup>
/**
 * Control panel to start and stop the arbitrage engine.
 */
import { ref, onMounted } from 'vue'
import { startArbit, stopArbit, fetchArbitStatus } from '@/services/arbit'

const status = ref({ running: false })

async function refresh() {
  status.value = await fetchArbitStatus()
}

async function start() {
  await startArbit()
  await refresh()
}

async function stop() {
  await stopArbit()
  await refresh()
}

onMounted(refresh)
</script>
