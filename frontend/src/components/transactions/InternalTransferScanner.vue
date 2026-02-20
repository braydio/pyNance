<!-- InternalTransferScanner.vue - Detect and confirm internal transfer pairs -->
<template>
  <div class="space-y-4">
    <div class="flex justify-end">
      <UiButton size="sm" @click="scan" :disabled="loading">
        {{ loading ? 'Scanning...' : 'Scan' }}
      </UiButton>
    </div>
    <div v-if="pairs.length" class="space-y-4">
      <div
        v-for="pair in pairs"
        :key="pair.transaction_id"
        class="flex items-start justify-between border p-4 rounded-md"
      >
        <div class="text-sm">
          <p class="font-medium">
            From:
            {{ formatAccount(pair) }}
            | {{ flowLabel(pair.amount) }} {{ formatSignedAmount(pair.amount) }}
          </p>
          <p class="text-gray-500">
            {{ pair.description }}
          </p>
          <p class="font-medium mt-2">
            To:
            {{ formatAccount(pair.counterpart) }}
            | {{ flowLabel(pair.counterpart.amount) }}
            {{ formatSignedAmount(pair.counterpart.amount) }}
          </p>
          <p class="text-gray-500">
            {{ pair.counterpart.description }}
          </p>
          <p class="text-xs text-gray-500 mt-2">
            Match score: {{ pair.match_score }} | Time delta: {{ pair.time_delta_hours }}h
          </p>
        </div>
        <UiButton variant="primary" @click="confirm(pair)">Mark Internal</UiButton>
      </div>
    </div>
    <p v-else-if="scanned" class="text-sm text-gray-500">No internal transfers found.</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/services/api.js'
import UiButton from '@/components/ui/Button.vue'

const pairs = ref([])
const loading = ref(false)
const scanned = ref(false)

async function scan() {
  loading.value = true
  try {
    const res = await api.scanInternalTransfers()
    pairs.value = res.pairs || []
  } catch (err) {
    console.error('Failed to scan internal transfers:', err)
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
