<template>
  <select
    :value="modelValue"
    @change="e => emit('update:modelValue', e.target.value)"
    class="input px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)]"
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
const props = defineProps({
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])
</script>
