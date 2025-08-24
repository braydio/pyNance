<template>
  <div :class="classes">
    <slot />
  </div>
</template>

<script setup lang="ts">
/**
 * BasePageLayout
 * Simple flex column wrapper that provides configurable padding and gap
 * utilities for page sections.
 *
 * Props:
 * - padding: tailwind padding utility class or `false` to disable (default `p-6`)
 * - gap: tailwind gap utility class (default `gap-6`)
 */
import { computed } from 'vue'

interface Props {
  /** Tailwind padding utility or `false` to remove padding */
  padding?: string | boolean
  /** Tailwind gap utility class applied to container */
  gap?: string
}

const props = withDefaults(defineProps<Props>(), {
  padding: true,
  gap: 'gap-6'
})

const paddingClass = computed(() => {
  if (props.padding === false) return ''
  if (typeof props.padding === 'string') return props.padding
  return 'p-6'
})

const classes = computed(() => {
  return ['flex', 'flex-col', paddingClass.value, props.gap].filter(Boolean)
})
</script>
