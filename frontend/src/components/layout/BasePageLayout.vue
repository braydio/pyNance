<template>
  <div :class="classes">
    <slot />
  </div>
</template>

<script setup lang="ts">
/**
 * BasePageLayout
 * Generic flex column container with configurable padding and gap.
 *
 * Props:
 * - padding: tailwind padding class or false to disable (default: 'p-6')
 * - gap: numeric or string tailwind gap value (e.g., 4 -> 'gap-4')
 */
import { computed } from 'vue'

interface Props {
  padding?: string | boolean
  gap?: string | number
}

const props = withDefaults(defineProps<Props>(), {
  padding: 'p-6',
})

const classes = computed(() => {
  const paddingClass =
    props.padding === false
      ? ''
      : typeof props.padding === 'string'
      ? props.padding
      : 'p-6'
  const gapClass =
    props.gap === undefined
      ? ''
      : typeof props.gap === 'number'
      ? `gap-${props.gap}`
      : `gap-${props.gap}`.replace('gap-gap-', 'gap-')
  return ['flex', 'flex-col', paddingClass, gapClass].filter(Boolean).join(' ')
})
</script>
