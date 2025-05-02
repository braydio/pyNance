<!-- ForecastAdjustmentsForm.vue -->
<template>
  <div class="border rounded p-4 bg-white">
    <h2>Custom Adjustment</h2>
    <form @submit.prevent="submit">
      <label>Label</label>
      <input v-model="label" type="text" class="block" />

      <label>Amount ($)</label>
      <input v-model.number="amount" type="number" class="block" />

      <button class="mt-2 px-2 py-1 bg-blue-500 text-white" type="submit">Add</button>
    </form>
  </div>
</template>
<script setup>
import { ref } from 'vue'
const emit = defineEmits(['addAdjustment'])
const label = ref('')
const amount = ref(0)

function submit() {
  emit('addAdjustment', { label: label.value, amount: amount.value })
  label.value = ''
  amount.value = 0
}
</script>
