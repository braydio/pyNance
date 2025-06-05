<template>
  <Modal @close="emit('close')">
    <template #title>
      {{ title }}
    </template>
    <template #body>
      <TransactionsTable :transactions="transactions" />
    </template>
  </Modal>
</template>

<script setup>
import Modal from '../ui/Modal.vue'
import TransactionsTable from '../tables/TransactionsTable.vue'

const props = defineProps({
  title: { type: String, default: '' },
  transactions: { type: Array, default: () => [] }
})
const emit = defineEmits(['close'])
</script>
