<template>
  <div :class="wrapperClasses">
    <slot name="header" />
    <slot />
  </div>
</template>

<script setup>
/**
 * BasePageLayout provides a full-page canvas with consistent background,
 * text color, and vertical spacing. Pages can optionally disable padding
 * or adjust gap between sections via props.
 */
import { computed } from 'vue'

const props = defineProps({
  padding: { type: Boolean, default: true },
  gap: { type: String, default: 'gap-6' },
})

const wrapperClasses = computed(() => [
  'base-page-layout flex flex-col min-h-screen',
  props.padding ? 'p-6' : '',
  props.gap,
])
</script>

<style scoped>
@reference "../../assets/css/main.css";
.base-page-layout {
  background-color: var(--page-bg);
  color: var(--theme-fg);
}
</style>

