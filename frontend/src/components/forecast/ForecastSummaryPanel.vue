<template>
  <div class="summary-panel">
    <h3 class="summary-header">Summary</h3>
    <div class="summary-grid">
      <div>
        <p class="label">Current Balance</p>
        <p class="value">${{ currentBalance.toFixed(2) }}</p>
      </div>
      <div>
        <p class="label">Manual Income</p>
        <input type="number" class="input" :value="localIncome"
          @input="emit('update:manualIncome', +$event.target.value)" />
      </div>
      <div>
        <p class="label">Liability Rate</p>
        <input type="number" class="input" :value="localRate"
          @input="emit('update:liabilityRate', +$event.target.value)" />
      </div>
    </div>
    <div class="summary-footer">
      <p>Net Delta: <strong>{{ netDelta }}</strong></p>
    </div>
  </div>
</template>

<script setup>
import { computed, toRef } from 'vue'

const props = defineProps({
  currentBalance: Number,
  manualIncome: Number,
  liabilityRate: Number,
  viewType: String
})

const emit = defineEmits(['update:manualIncome', 'update:liabilityRate'])

const localIncome = toRef(props, 'manualIncome')
const localRate = toRef(props, 'liabilityRate')

const netDelta = computed(() => {
  return ((localIncome.value || 0) - (localRate.value || 0)).toFixed(2)
})
</script>

<style scoped>
.summary-panel {
  background: var(--surface);
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid var(--divider);
}

.summary-header {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
}

.label {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.value {
  font-weight: bold;
}

.input {
  width: 100%;
  padding: 0.4rem;
  font-size: 0.9rem;
  border: 1px solid var(--divider);
  border-radius: 0.375rem;
  background: var(--input-bg);
  color: var(--theme-fg);
}

.summary-footer {
  margin-top: 1rem;
  font-size: 0.9rem;
}
</style>
