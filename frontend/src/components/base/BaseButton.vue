<template>
  <button :type="type" :disabled="disabled" :class="buttonClasses" @click="$emit('click', $event)">
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'

/**
 * Shared button primitive that owns geometry, border, and focus-ring states.
 */
const props = defineProps({
  type: { type: String, default: 'button' },
  variant: {
    type: String,
    default: 'outline',
    validator: (value) => ['solid', 'outline', 'ghost'].includes(value),
  },
  tone: {
    type: String,
    default: 'neutral',
    validator: (value) => ['neutral', 'accent', 'danger', 'success'].includes(value),
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md'].includes(value),
  },
  radius: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg', 'pill'].includes(value),
  },
  active: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

defineEmits(['click'])

const radiusClasses = {
  sm: 'ui-radius-1',
  md: 'ui-radius-2',
  lg: 'ui-radius-3',
  pill: 'rounded-full',
}

const sizeClasses = {
  sm: 'px-2.5 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
}

const toneClasses = {
  neutral: {
    solid: 'bg-surface-1 border-strong text-primary',
    outline:
      'bg-surface-1 border-subtle text-secondary hover:border-strong hover:text-primary hover-surface',
    ghost: 'border-transparent text-secondary hover-surface hover:text-primary',
    active: 'bg-surface-1 border-strong text-primary',
  },
  accent: {
    solid:
      'border-[color:var(--accent-primary)] bg-[color:var(--accent-primary)] text-[color:var(--accent-primary-contrast)]',
    outline:
      'border-[color:var(--accent-primary)] text-[color:var(--accent-primary)] hover:bg-[color:var(--accent-primary)] hover:text-[color:var(--accent-primary-contrast)]',
    ghost:
      'border-transparent text-[color:var(--accent-primary)] hover:bg-[color:var(--accent-surface)]',
    active:
      'bg-[color:var(--accent-primary)] border-[color:var(--accent-primary)] text-[color:var(--accent-primary-contrast)]',
  },
  danger: {
    solid:
      'border-[color:var(--color-accent-red)] bg-[color:var(--color-accent-red)] text-[color:var(--color-bg-dark)]',
    outline:
      'border-[color:var(--color-accent-red)] text-[color:var(--color-accent-red)] hover:bg-[color:var(--color-accent-red)] hover:text-[color:var(--color-bg-dark)]',
    ghost:
      'border-transparent text-[color:var(--color-accent-red)] hover:bg-[color:var(--color-accent-red)]/20',
    active:
      'bg-[color:var(--color-accent-red)] border-[color:var(--color-accent-red)] text-[color:var(--color-bg-dark)]',
  },
  success: {
    solid:
      'border-[color:var(--color-accent-green)] bg-[color:var(--color-accent-green)] text-[color:var(--color-bg-dark)]',
    outline:
      'border-[color:var(--color-accent-green)] text-[color:var(--color-accent-green)] hover:bg-[color:var(--color-accent-green)] hover:text-[color:var(--color-bg-dark)]',
    ghost:
      'border-transparent text-[color:var(--color-accent-green)] hover:bg-[color:var(--color-accent-green)]/20',
    active:
      'bg-[color:var(--color-accent-green)] border-[color:var(--color-accent-green)] text-[color:var(--color-bg-dark)]',
  },
}

const buttonClasses = computed(() => {
  const tone = toneClasses[props.tone]
  const variantClasses = props.active ? tone.active : tone[props.variant]
  return [
    'inline-flex items-center justify-center gap-1.5 border font-semibold uppercase tracking-wide transition focus-ring disabled:cursor-not-allowed disabled:opacity-60',
    radiusClasses[props.radius],
    sizeClasses[props.size],
    variantClasses,
  ]
})
</script>
