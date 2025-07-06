<template>
  <div class="flex justify-between items-center gap-4 flex-wrap mb-3 w-full">
    <!-- Left: Icon + Title -->
    <div class="flex items-center gap-2 min-w-0">
      <slot name="icon"></slot>
      <h2 class="text-xl font-semibold tracking-tight text-[var(--color-text-light)] truncate">
        <slot name="title"></slot>
      </h2>
    </div>
    <!-- Center: Controls -->
    <div class="flex gap-2 items-center flex-shrink-0">
      <slot name="controls"></slot>
    </div>
    <!-- Right: Summary (if present) -->
    <div v-if="$slots.summary"
      class="chart-summary bg-[var(--color-bg-secondary)] px-4 py-2 rounded font-mono text-[var(--color-text-muted)] z-10 text-right border-2 border-[var(--divider)] shadow backdrop-blur-sm transition ml-auto min-w-[150px]">
      <slot name="summary"></slot>
    </div>
  </div>
</template>

<script setup>
/**
 * ChartWidgetTopBar
 * Shared top bar for chart widgets. Usage:
 *  <ChartWidgetTopBar>
 *    <template #icon>...</template>
 *    <template #title>Chart Title</template>
 *    <template #controls>...</template>
 *    <template #summary>...</template>
 *  </ChartWidgetTopBar>
 */
</script>

<style scoped>
@import "../../assets/css/main.css";

.chart-summary {
  min-width: 150px;
  max-width: 100vw;
  white-space: nowrap;
}
</style>
