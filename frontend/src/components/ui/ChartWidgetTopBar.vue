<template>
  <div class="flex justify-between items-center gap-4 flex-wrap mb-3 w-full">
    <div class="flex items-center gap-2 min-w-0">
      <slot name="icon"></slot>
      <h2 class="text-xl font-semibold tracking-tight text-[var(--color-text-light)] truncate">
        <slot name="title"></slot>
      </h2>
    </div>
    <div class="flex gap-2 items-center">
      <slot name="controls"></slot>
    </div>
    <div v-if="$slots.summary"
      class="chart-summary bg-[var(--color-bg-secondary)] px-4 py-2 rounded font-mono text-[var(--color-text-muted)] z-10 text-right border-2 border-[var(--divider)] shadow backdrop-blur-sm transition ml-auto min-w-[150px]">
      <slot name="summary"></slot>
    </div>
  </div>
</template>

<script setup>
/**
 * ChartWidgetTopBar
 * Reusable top bar for chart cards. Accepts named slots:
 *  - icon: optional SVG/icon at far left
 *  - title: chart title
 *  - controls: date pickers, zoom, etc
 *  - summary: right-aligned summary/total info
 */
</script>

<style scoped>
@import "../../assets/css/main.css";

.chart-summary {
  min-width: 150px;
}
</style>
