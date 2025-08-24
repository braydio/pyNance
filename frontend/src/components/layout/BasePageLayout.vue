<template>
  <div
    class="base-page-layout"
    :style="{ padding: paddingStyle, gap: spacingStyle }"
  >
    <slot name="header" />
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'
/**
 * BasePageLayout provides a reusable page wrapper with common
 * background, text color, spacing, and padding. Header content can
 * be injected via the `header` slot while default slot renders the
 * body. Padding and spacing can be customized with props.
 */
const props = defineProps({
  // Optional padding applied to the page container
  padding: { type: [String, Number], default: '1.5rem' },
  // Optional vertical spacing between header and body elements
  spacing: { type: [String, Number], default: '1.5rem' },
})

const paddingStyle = computed(() =>
  typeof props.padding === 'number' ? `${props.padding}rem` : props.padding
)
const spacingStyle = computed(() =>
  typeof props.spacing === 'number' ? `${props.spacing}rem` : props.spacing
)
</script>

<style scoped>
.base-page-layout {
  background-color: var(--page-bg);
  color: var(--theme-fg);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
