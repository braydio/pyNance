<template>
  <select :value="modelValue" :disabled="disabled" :class="selectClasses" @change="handleChange">
    <slot />
  </select>
</template>

<script setup>
import { computed } from 'vue'

/**
 * Shared select primitive for compact controls with unified border/focus behavior.
 */
const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
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

const emit = defineEmits(['update:modelValue', 'change'])

const selectClasses = computed(() => {
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
    'border bg-surface-1 border-subtle text-secondary focus-ring outline-none disabled:cursor-not-allowed disabled:opacity-70',
    radius[props.radius],
    size[props.size],
  ]
})

function handleChange(event) {
  emit('update:modelValue', event.target.value)
  emit('change', event)
}
</script>
