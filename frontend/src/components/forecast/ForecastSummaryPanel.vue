<template>
  <div class="forecast-card">
    <h2 class="section-title">Summary</h2>
    <div class="text-base space-y-1">
      <p><strong>Current Balance:</strong> ${{ currentBalance.toFixed(2) }}</p>
      <p><strong>Projected Delta:</strong> ${{ computedDelta.toFixed(2) }}</p>
      <p><strong>Projected Balance:</strong> ${{ (currentBalance + computedDelta).toFixed(2) }}</p>
    </div>

    <div class="input-group">
      <label class="form-label">Manual Recurring Income ($)</label>
      <input type="number" v-model.number="localIncome" class="form-input"
        @input="$emit('update:manualIncome', localIncome)" />

      <label class="form-label mt-4">Liability Rate (%)</label>
      <input type="number" v-model.number="localRate" class="form-input"
        @input="$emit('update:liabilityRate', localRate)" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps(['currentBalance', 'manualIncome', 'liabilityRate'])

const localIncome = ref(props.manualIncome)
const localRate = ref(props.liabilityRate)

const computedDelta = computed(() =>
  localIncome.value - (props.currentBalance * localRate.value / 100)
)
</script>

<style scoped>
.forecast-card {
  @apply bg-white rounded-2xl shadow p-6 space-y-4;
}

.section-title {
  @apply text-xl font-semibold mb-2;
}

.input-group {
  @apply space-y-4 pt-4;
}

.form-label {
  @apply block text-sm font-medium text-gray-600;
}

.form-input {
  @apply w-full border border-gray-300 p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-400;
}
</style>
