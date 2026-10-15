<!-- InternalTransferScanner.vue - Detect and confirm internal transfer pairs -->
<template>
  <div class="space-y-4">
    <div class="flex justify-end">
      <UiButton type="button" size="sm" :disabled="loading" @click="scan">
        {{ loading ? 'Scanning...' : 'Scan' }}
      </UiButton>
    </div>
    <div v-if="pairs.length" class="space-y-4">
      <div
        v-for="pair in pairs"
        :key="pair.transaction_id"
        class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between border p-4 rounded-md"
      >
        <div class="text-sm">
          <p class="font-medium">
            From:
            {{ formatAccount(pair) }}
            | {{ flowLabel(pair.amount) }} {{ formatSignedAmount(pair.amount) }}
          </p>
          <p class="text-muted">
            {{ pair.description }}
          </p>
          <p class="font-medium mt-2">
            To:
            {{ formatAccount(pair.counterpart) }}
            | {{ flowLabel(pair.counterpart.amount) }}
            {{ formatSignedAmount(pair.counterpart.amount) }}
          </p>
          <p class="text-muted">
            {{ pair.counterpart.description }}
          </p>
          <p class="text-sm text-muted mt-2">
            Match score: {{ pair.match_score }} | Time delta: {{ pair.time_delta_hours }}h
          </p>
        </div>
        <UiButton type="button" variant="primary" @click="confirm(pair)">Mark Internal</UiButton>
      </div>
    </div>
    <p v-else-if="scanError" class="text-sm text-negative" role="alert">
      Unable to scan for internal transfers. Try again.
    </p>
    <p v-else-if="scanned" class="text-sm text-muted" role="status">No internal transfers found.</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/services/api.js'
import UiButton from '@/components/ui/Button.vue'

const pairs = ref([])
const loading = ref(false)
const scanned = ref(false)
const scanError = ref(false)

async function scan() {
  loading.value = true
  scanError.value = false
  try {
    const res = await api.scanInternalTransfers()
    pairs.value = res.pairs || []
  } catch (err) {
    console.error('Failed to scan internal transfers:', err)
    scanError.value = true
  } finally {
    scanned.value = true
    loading.value = false
  }
}

async function confirm(pair) {
  try {
    await api.updateTransaction({
      transaction_id: pair.transaction_id,
      is_internal: true,
      counterpart_transaction_id: pair.counterpart_id,
      flag_counterpart: true,
    })
    pairs.value = pairs.value.filter((p) => p.transaction_id !== pair.transaction_id)
  } catch (err) {
    console.error('Failed to mark transaction as internal:', err)
  }
}

function formatSignedAmount(amount) {
  const numeric = Number(amount) || 0
  const absolute = Math.abs(numeric)
  const symbol = numeric >= 0 ? '+' : '-'
  return `${symbol}$${absolute.toFixed(2)}`
}

function flowLabel(amount) {
  const numeric = Number(amount) || 0
  return numeric >= 0 ? 'Inflow' : 'Outflow'
}

function formatAccount(side) {
  const institution = side?.institution_name || 'Unknown Institution'
  const account = side?.account_name || side?.account_id || 'Unknown Account'
  return `${institution} / ${account}`
}
</script>
