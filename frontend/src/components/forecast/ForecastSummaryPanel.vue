<template>
  <div class="bg-white rounded-2xl shadow p-6 space-y-4">
    <h2 class="text-xl font-semibold">Summary</h2>
    <div class="text-base space-y-1">
      <p><strong>Current Balance:</strong> ${{ currentBalance.toFixed(2) }}</p>
      <p><strong>Projected Delta:</strong> ${{ computedDelta.toFixed(2) }}</p>
      <p><strong>Projected Balance:</strong> ${{ (currentBalance + computedDelta).toFixed(2) }}</p>
    </div>

    <div class="space-y-4 pt-2">
      <div>
        <label class="text-sm font-medium text-gray-600 block">Manual Recurring Income ($)</label>
        <input type="number" v-model.number="localIncome"
          class="w-full border p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-300"
          @input="$emit('update:manualIncome', localIncome)" />
      </div>

      <div>
        <label class="text-sm font-medium text-gray-600 block">Liability Rate (%)</label>
        <input type="number" v-model.number="localRate"
          class="w-full border p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-300"
          @input="$emit('update:liabilityRate', localRate)" />
      </div>
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
