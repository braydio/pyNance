<template>
  <component :is="tag" :class="chipClasses">
    <slot />
  </component>
</template>

<script setup>
import { computed } from 'vue'

/**
 * Compact status/control chip primitive with controlled radius and state classes.
 */
const props = defineProps({
  tag: { type: String, default: 'span' },
  tone: {
    type: String,
    default: 'neutral',
    validator: (value) => ['neutral', 'accent', 'info', 'success'].includes(value),
  },
  active: { type: Boolean, default: false },
  radius: {
    type: String,
    default: 'pill',
    validator: (value) => ['sm', 'md', 'pill'].includes(value),
  },
})

const chipClasses = computed(() => {
  const radius = {
    sm: 'ui-radius-1',
    md: 'ui-radius-2',
    pill: 'rounded-full',
  }

  const toneClasses = {
    neutral: props.active
      ? 'bg-surface-1 border-strong text-primary'
      : 'bg-surface-2 border-subtle text-secondary',
    accent: props.active
      ? 'bg-[color:var(--accent-primary)] border-[color:var(--accent-primary)] text-[color:var(--accent-primary-contrast)]'
      : 'bg-[color:var(--accent-surface)] border-[color:var(--accent-primary)]/60 text-[color:var(--accent-primary)]',
    info: props.active ? 'ui-pill-info border-strong' : 'ui-pill-info',
    success: props.active ? 'ui-pill-success border-strong' : 'ui-pill-success',
  }

  return [
    'inline-flex items-center gap-1.5 border px-3 py-1 text-xs font-semibold transition',
    radius[props.radius],
    toneClasses[props.tone],
  ]
})
</script>
