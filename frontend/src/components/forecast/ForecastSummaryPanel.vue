<template>
  <div class="bg-white rounded-2xl shadow p-6 space-y-4">
    <h2 class="text-xl font-semibold">Summary ({{ viewType }} View)</h2>

    <div class="text-base space-y-1">
      <p><strong>Current Balance:</strong> ${{ currentBalance.toFixed(2) }}</p>
      <p><strong>Forecasted Delta:</strong> ${{ computedDelta.toFixed(2) }}</p>
      <p><strong>Projected Balance:</strong> ${{ projectedBalance.toFixed(2) }}</p>
    </div>

    <div class="space-y-4 pt-4">
      <div>
        <label class="block text-sm font-medium text-gray-600">Manual Recurring Income ($)</label>
        <input type="number" v-model.number="localIncome" @input="$emit('update:manualIncome', localIncome)"
          class="w-full border border-gray-300 p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-400" />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-600 mt-2">Liability Rate (%)</label>
        <input type="number" v-model.number="localRate" @input="$emit('update:liabilityRate', localRate)"
          class="w-full border border-gray-300 p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-400" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  currentBalance: Number,
  manualIncome: Number,
  liabilityRate: Number,
  viewType: String
})

const localIncome = ref(props.manualIncome)
const localRate = ref(props.liabilityRate)
const multiplier = computed(() => props.viewType === 'Year' ? 12 : 1)

const computedDelta = computed(() => {
  const income = localIncome.value * multiplier.value
  const liabilities = props.currentBalance * (localRate.value / 100)
  return income - liabilities
})

const projectedBalance = computed(() =>
  props.currentBalance + computedDelta.value
)
</script>

<style scoped>
/* None required — all Tailwind inline */
</style>
