<template>
  <!-- Display a table of transactions in a small pop modal -->
  <Modal size="lg" @close="emit('close')">
    <template #title>
      {{ title }}
    </template>
    <template #body>
      <TransactionsTable :transactions="transactions" />
    </template>
  </Modal>
</template>

<script setup>
// Modal wrapper showing a transactions table.
import Modal from '../ui/Modal.vue'
import TransactionsTable from '../tables/TransactionsTable.vue'

defineProps({
  title: { type: String, default: '' },
  transactions: { type: Array, default: () => [] }
})
const emit = defineEmits(['close'])
</script>
