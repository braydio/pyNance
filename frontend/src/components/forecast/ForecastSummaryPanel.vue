<template>
  <div class="summary-panel bg-white p-4 rounded shadow space-y-2">
    <h2 class="text-lg font-semibold">Summary</h2>
    <p>Current Balance: ${{ currentBalance.toFixed(2) }}</p>
    <p>Projected Change: ${{ computedDelta.toFixed(2) }}</p>
    <p>Projected Ending: ${{ projectedBalance.toFixed(2) }}</p>

    <div class="space-y-2">
      <label class="block text-sm">
        Manual Income
        <input type="number" class="input" v-model.number="localIncome"
          @blur="$emit('update:manualIncome', localIncome)" />
      </label>

      <label class="block text-sm">
        Liability Rate
        <input type="number" class="input" v-model.number="localRate"
          @blur="$emit('update:liabilityRate', localRate)" />
      </label>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  currentBalance: Number,
  manualIncome: Number,
  liabilityRate: Number,
  viewType: String,
  forecastItems: Array,
})

const emit = defineEmits(['update:manualIncome', 'update:liabilityRate'])

const localIncome = ref(props.manualIncome || 0)
const localRate = ref(props.liabilityRate || 0)

watch(() => props.manualIncome, (v) => localIncome.value = v)
watch(() => props.liabilityRate, (v) => localRate.value = v)

const computedDelta = computed(() => {
  return props.forecastItems.reduce((sum, item) => sum + item.amount, 0) +
    (localIncome.value || 0) - (localRate.value || 0)
})

const projectedBalance = computed(() => {
  return (props.currentBalance || 0) + computedDelta.value
})
</script>

<style scoped>
.summary-panel {
  border: 1px solid #ccc;
}

.input {
  border: 1px solid #ccc;
  padding: 0.4rem;
  width: 100%;
  margin-top: 0.2rem;
}
</style>
