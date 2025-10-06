<template>
  <TransactionModal
    :show="show"
    :transactions="transactions"
    :subtitle="subtitle"
    kind="date"
    :show-date-column="false"
    :hide-category-visuals="false"
    @close="$emit('close')"
  />
  
</template>

<script setup>
import TransactionModal from './TransactionModal.vue'

defineProps({
  show: { type: Boolean, default: false },
  transactions: { type: Array, default: () => [] },
  // Date label shown under the title, e.g., '2025-01-15'
  subtitle: { type: String, default: '' },
})

defineEmits(['close'])
</script>

