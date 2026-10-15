<template>
  <select
    :value="modelValue"
    @change="(e) => emit('update:modelValue', e.target.value)"
    class="input select"
    aria-label="Filter by transaction type"
    data-testid="type-select"
  >
    <option value="">All Types</option>
    <option value="credit">Credit</option>
    <option value="debit">Debit</option>
  </select>
</template>

<script setup>
/**
 * Selector for transaction type filter (credit/debit/all).
 */
defineProps({
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])
</script>
