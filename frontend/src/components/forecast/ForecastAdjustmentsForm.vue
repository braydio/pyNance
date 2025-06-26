<template>
  <div class="adjustments-form">
    <h3 class="form-title">Add Adjustment</h3>
    <form @submit.prevent="submitAdjustment" class="form-grid">
      <input v-model="label" type="text" class="input" placeholder="Label" required />
      <input v-model.number="amount" type="number" class="input" placeholder="Amount" required />
      <button type="submit" class="submit-button">Add</button>
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
@reference "../../assets/css/main.css";
.adjustments-form {
  background: var(--surface);
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid var(--divider);
}

.form-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.form-grid {
  display: grid;
  grid-template-columns: 2fr 1fr auto;
  gap: 0.5rem;
}

.input {
  padding: 0.5rem;
  font-size: 0.875rem;
  border: 1px solid var(--divider);
  border-radius: 0.375rem;
  background: var(--input-bg);
  color: var(--theme-fg);
}

.submit-button {
  background-color: var(--primary);
  color: white;
  padding: 0.5rem 1rem;
  font-weight: 600;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
}

.submit-button:hover {
  background-color: var(--primary-dark);
}
</style>
