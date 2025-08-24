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
            {{ pair.description }} ({{ formatAmount(pair.amount) }})
          </p>
          <p class="text-gray-500">
            ↔
            {{ pair.counterpart.description }}
            ({{ formatAmount(pair.counterpart.amount) }})
          </p>
        </div>
        <UiButton variant="primary" @click="confirm(pair)">Mark Internal</UiButton>
      </div>
    </div>
    <p v-else-if="scanned" class="text-sm text-gray-500">
      No internal transfers found.
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/services/api.js'
import UiButton from '@/components/ui/Button.vue'
import { formatAmount } from '@/utils/format'

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
    pairs.value = pairs.value.filter(
      (p) => p.transaction_id !== pair.transaction_id
    )
  } catch (err) {
    console.error('Failed to mark transaction as internal:', err)
  }
}
</script>

