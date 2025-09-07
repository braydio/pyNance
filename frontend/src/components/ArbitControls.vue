<template>
  <div>
    <button class="start-btn" @click="start">Start</button>
    <button class="stop-btn" @click="stop">Stop</button>
    <div>Status: {{ status.running ? 'running' : 'stopped' }}</div>
    <div class="alert-config">
      <input v-model.number="threshold" type="number" placeholder="Alert threshold" />
      <button class="alert-btn" @click="checkAlert">Check Profit</button>
    </div>
  </div>
</template>

<script setup>
/**
 * Control panel to start and stop the arbitrage engine.
 */
import { ref, onMounted } from 'vue'
import { startArbit, stopArbit, fetchArbitStatus, postArbitAlert } from '@/services/arbit'

const status = ref({ running: false })
const threshold = ref(0)

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

async function checkAlert() {
  await postArbitAlert(threshold.value)
}

onMounted(refresh)
</script>
