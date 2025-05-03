<template>
  <div class="adjustments-form">
    <h2>Add Adjustment</h2>
    <form @submit.prevent="submitAdjustment">
      <input v-model="label" placeholder="Label" required />
      <input v-model.number="amount" type="number" placeholder="Amount" required />
      <button type="submit">Add</button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['add-adjustment'])

const label = ref('')
const amount = ref(0)

function submitAdjustment() {
  if (label.value && amount.value) {
    emit('add-adjustment', { label: label.value, amount: amount.value })
    label.value = ''
    amount.value = 0
  }
}
</script>

<style scoped>
.adjustments-form {
  padding: 1rem;
  border: 1px solid #ccc;
}
</style>
