<template>
  <div>
    <div class="start-config">
      <div class="field">
        <label for="start-threshold">Minimum Spread (%)</label>
        <input
          id="start-threshold"
          data-test="start-threshold"
          v-model.number="startThreshold"
          type="number"
          min="0"
          step="0.01"
          placeholder="Minimum spread required"
        />
        <p class="help-text">Trades trigger once market spread exceeds this percentage.</p>
        <p v-if="startErrors.threshold" class="error">{{ startErrors.threshold }}</p>
      </div>
      <div class="field">
        <label for="start-fee">Exchange Fee (%)</label>
        <input
          id="start-fee"
          data-test="start-fee"
          v-model.number="startFee"
          type="number"
          min="0"
          step="0.01"
          placeholder="Combined taker fees"
        />
        <p class="help-text">Include maker/taker and withdrawal fees expected per trade.</p>
        <p v-if="startErrors.fee" class="error">{{ startErrors.fee }}</p>
      </div>
    </div>
    <button class="start-btn" @click="start">Start</button>
    <button class="stop-btn" @click="stop">Stop</button>
    <div>Status: {{ status.running ? 'running' : 'stopped' }}</div>
    <div class="alert-config">
      <input
        v-model.number="alertThreshold"
        type="number"
        min="0"
        step="0.01"
        placeholder="Alert threshold"
      />
      <button class="alert-btn" @click="checkAlert">Check Profit</button>
    </div>
  </div>
</template>

<script setup>
/**
 * Control panel to configure spread/fee requirements and control the arbitrage engine.
 */
import { ref, onMounted } from 'vue'
import { startArbit, stopArbit, fetchArbitStatus, postArbitAlert } from '@/services/arbit'

const status = ref({ running: false })
const startThreshold = ref(null)
const startFee = ref(null)
const startErrors = ref({})
const alertThreshold = ref(0)

async function refresh() {
  status.value = await fetchArbitStatus()
}

async function start() {
  const { valid, threshold, fee } = validateStartConfig()
  if (!valid) {
    return
  }
  await startArbit(threshold, fee)
  await refresh()
}

async function stop() {
  await stopArbit()
  await refresh()
}

async function checkAlert() {
  await postArbitAlert(alertThreshold.value)
}

function validateStartConfig() {
  const errors = {}
  const thresholdNumber = Number(startThreshold.value)
  const feeNumber = Number(startFee.value)

  if (
    startThreshold.value === null ||
    startThreshold.value === '' ||
    Number.isNaN(thresholdNumber)
  ) {
    errors.threshold = 'Enter the minimum spread percentage required to start trading.'
  } else if (thresholdNumber <= 0) {
    errors.threshold = 'Spread threshold must be greater than 0%.'
  }

  if (startFee.value === null || startFee.value === '' || Number.isNaN(feeNumber)) {
    errors.fee = 'Provide the expected percentage cost of executing the trade.'
  } else if (feeNumber < 0) {
    errors.fee = 'Exchange fees cannot be negative.'
  }

  startErrors.value = errors
  return {
    valid: Object.keys(errors).length === 0,
    threshold: thresholdNumber,
    fee: feeNumber,
  }
}

onMounted(refresh)
</script>
