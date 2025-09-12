<!--
  BillList.vue
  -------------
  Display a list of bills with edit and delete actions.
-->

<template>
  <ul class="bill-list">
    <li v-for="bill in bills" :key="bill.id" class="bill-item">
      <span class="bill-name">{{ bill.name }}</span>
      <span class="bill-amount">{{ formatAmount(bill.amount) }}</span>
      <span class="bill-due">Due: {{ bill.due_date }}</span>
      <button class="btn-edit" @click="emit('edit', bill)">Edit</button>
      <button class="btn-delete" @click="emit('delete', bill.id)">Delete</button>
    </li>
  </ul>
</template>

<script setup>
/**
 * Render a list of bills and provide edit/delete hooks to the parent.
 *
 * Emits:
 * - `edit` with the full bill object.
 * - `delete` with the bill identifier.
 */
import { formatAmount } from '@/utils/format'

const props = defineProps({
  bills: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['edit', 'delete'])
</script>

<style scoped>
.bill-list {
  list-style: none;
  padding: 0;
}

.bill-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.bill-name {
  font-weight: 500;
}

.bill-amount,
.bill-due {
  margin-left: auto;
  margin-right: 0.5rem;
}

.btn-edit,
.btn-delete {
  margin-left: 0.25rem;
  cursor: pointer;
}
</style>

