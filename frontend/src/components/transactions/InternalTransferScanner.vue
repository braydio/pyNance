<!-- InternalTransferScanner.vue - Detect and confirm internal transfer pairs -->
<template>
  <Card class="p-6 space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold">Internal Transfers</h2>
      <UiButton @click="scan" :disabled="loading">
        {{ loading ? 'Scanning...' : 'Scan' }}
      </UiButton>
    </div>
    <div v-if="pairs.length" class="space-y-4">
      <div
        v-for="pair in pairs"
        :key="pair.transaction_id"
        class="flex items-start justify-between border p-4 rounded"
      >
        <div class="text-sm">
          <p class="font-medium">
            {{ pair.description }} ({{ formatAmount(pair.amount) }})
          </p>
          <p class="text-muted">
            ↔
            {{ pair.counterpart.description }}
            ({{ formatAmount(pair.counterpart.amount) }})
          </p>
        </div>
        <UiButton variant="primary" @click="confirm(pair)">Mark Internal</UiButton>
      </div>
    </div>
    <p v-else-if="scanned" class="text-muted">No internal transfers found.</p>
  </Card>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/services/api.js'
import UiButton from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
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

<style scoped>
.text-muted {
  color: var(--color-text-muted);
}
</style>

