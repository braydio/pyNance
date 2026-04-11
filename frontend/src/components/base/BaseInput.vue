<template>
  <input
    :value="modelValue"
    :type="type"
    :disabled="disabled"
    :placeholder="placeholder"
    :min="min"
    :max="max"
    :class="inputClasses"
    @input="$emit('update:modelValue', $event.target.value)"
    @keyup.enter="$emit('enter', $event)"
  />
</template>

<script setup>
import { computed } from 'vue'

/**
 * Shared text/number input primitive with consistent angular geometry and focus rings.
 */
const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  min: { type: [String, Number], default: undefined },
  max: { type: [String, Number], default: undefined },
  disabled: { type: Boolean, default: false },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md'].includes(value),
  },
  radius: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value),
  },
})

defineEmits(['update:modelValue', 'enter'])

const inputClasses = computed(() => {
  const radius = {
    sm: 'ui-radius-1',
    md: 'ui-radius-2',
    lg: 'ui-radius-3',
  }
  const size = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
  }

  return [
    'border bg-surface-1 border-subtle text-primary focus-ring outline-none disabled:cursor-not-allowed disabled:opacity-70',
    radius[props.radius],
    size[props.size],
  ]
})
</script>
