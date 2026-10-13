<template>
  <div :class="classes">
    <slot />
  </div>
</template>

<script setup>
/**
 * BasePageLayout
 * Vertical flow container for page sections. Global max width and horizontal
 * gutters are owned by AppLayout, so this layer only adds vertical spacing.
 *
 * Props:
 * - padding: Tailwind padding utilities or `false` to disable (default
 *   `py-6`)
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
  return 'py-6'
})

const classes = computed(() => {
  return ['w-full', 'flex', 'flex-col', paddingClass.value, props.gap].filter(Boolean)
})
</script>
