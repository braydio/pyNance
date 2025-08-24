<template>
  <div :class="classes">
    <slot />
  </div>
</template>

<script setup>
/**
 * BasePageLayout
 * Responsive container that clamps width and applies consistent horizontal
 * gutters for page sections.
 *
 * Props:
 * - padding: Tailwind padding utilities or `false` to disable (default
 *   `px-4 sm:px-6 lg:px-8 py-6`)
 * - gap: Tailwind gap utility class applied to container (default `gap-6`)
 */
import { computed } from 'vue'

const props = defineProps({
  /** Tailwind padding utility or `false` to remove padding */
  padding: { type: [String, Boolean], default: true },
  /** Tailwind gap utility class applied to container */
  gap: { type: String, default: 'gap-6' },
})

const paddingClass = computed(() => {
  if (props.padding === false) return ''
  if (typeof props.padding === 'string') return props.padding
  return 'px-4 sm:px-6 lg:px-8 py-6'
})

const classes = computed(() => {
  return [
    'w-full',
    'max-w-7xl',
    'mx-auto',
    'flex',
    'flex-col',
    paddingClass.value,
    props.gap,
  ].filter(Boolean)
})
</script>
