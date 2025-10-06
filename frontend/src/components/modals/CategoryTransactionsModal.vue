<template>
  <TransactionModal
    :show="show"
    :transactions="transactions"
    :subtitle="subtitle"
    kind="category"
    :show-date-column="true"
    :hide-category-visuals="false"
    @close="$emit('close')"
  />
</template>

<script setup>
import TransactionModal from './TransactionModal.vue'

defineProps({
  show: { type: Boolean, default: false },
  transactions: { type: Array, default: () => [] },
  // Category label shown under the title, e.g., 'Groceries'
  subtitle: { type: String, default: '' },
})

defineEmits(['close'])
</script>
