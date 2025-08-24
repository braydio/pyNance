<template>
  <div class="base-page-layout min-h-screen">
    <div :class="wrapperClasses">
      <slot name="header" />
      <slot />
    </div>
  </div>
</template>

<script setup>
/**
 * BasePageLayout provides a full-page canvas with consistent background
 * and text color. Content is centered within a max-width container and
 * can optionally disable padding or adjust vertical gap between sections.
 */
import { computed } from 'vue'

const props = defineProps({
  padding: { type: Boolean, default: true },
  gap: { type: String, default: 'gap-6' },
})

const wrapperClasses = computed(() => [
  'flex flex-col w-full max-w-screen-xl mx-auto',
  props.padding ? 'px-6 py-6' : '',
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

