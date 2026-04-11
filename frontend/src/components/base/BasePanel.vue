<template>
  <component :is="tag" :class="panelClasses">
    <slot />
  </component>
</template>

<script setup>
import { computed } from 'vue'

/**
 * Shared panel primitive for section shells, cards, and grouped control surfaces.
 */
const props = defineProps({
  tag: { type: String, default: 'div' },
  surface: {
    type: String,
    default: 'secondary',
    validator: (value) => ['primary', 'secondary', 'tertiary'].includes(value),
  },
  borderTone: {
    type: String,
    default: 'subtle',
    validator: (value) =>
      ['subtle', 'strong', 'accent-cyan', 'accent-red', 'accent-yellow', 'accent-green'].includes(
        value,
      ),
  },
  radius: {
    type: String,
    default: 'lg',
    validator: (value) => ['sm', 'md', 'lg'].includes(value),
  },
  padding: {
    type: String,
    default: 'md',
    validator: (value) => ['none', 'sm', 'md', 'lg'].includes(value),
  },
  shadow: {
    type: String,
    default: 'md',
    validator: (value) => ['none', 'sm', 'md', 'lg'].includes(value),
  },
})

const panelClasses = computed(() => {
  const surface = {
    primary: 'bg-surface-1',
    secondary: 'bg-surface-2',
    tertiary: 'bg-surface-3',
  }
  const borderTone = {
    subtle: 'border border-subtle',
    strong: 'border border-strong',
    'accent-cyan': 'border-2 border-[var(--color-accent-cyan)]',
    'accent-red': 'border-2 border-[var(--color-accent-red)]',
    'accent-yellow': 'border-2 border-[var(--color-accent-yellow)]',
    'accent-green': 'border-2 border-[var(--color-accent-green)]',
  }
  const radius = {
    sm: 'ui-radius-1',
    md: 'ui-radius-2',
    lg: 'ui-radius-3',
  }
  const padding = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  }
  const shadow = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-lg',
    lg: 'shadow-2xl',
  }

  return [
    surface[props.surface],
    borderTone[props.borderTone],
    radius[props.radius],
    padding[props.padding],
    shadow[props.shadow],
  ]
})
</script>
