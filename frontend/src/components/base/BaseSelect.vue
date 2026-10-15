<template>
  <select
    :value="modelValue"
    :disabled="disabled"
    :aria-invalid="invalid ? 'true' : undefined"
    :aria-describedby="describedby || undefined"
    :class="selectClasses"
    @change="handleChange"
  >
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
  invalid: { type: Boolean, default: false },
  describedby: { type: String, default: '' },
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
    sm: 'min-h-[var(--control-height-sm)] px-3 py-1 text-sm',
    md: 'min-h-[var(--control-height)] px-3 py-1.5 text-sm',
  }

  return [
    'block w-full min-w-0 max-w-full border bg-surface-1 border-[color:var(--control-border)] text-primary focus-ring outline-none disabled:cursor-not-allowed disabled:opacity-70',
    props.invalid && 'border-[color:var(--text-negative)]',
    radius[props.radius],
    size[props.size],
  ]
})

function handleChange(event) {
  emit('update:modelValue', event.target.value)
  emit('change', event)
}
</script>
