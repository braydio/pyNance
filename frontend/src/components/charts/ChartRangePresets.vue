<template>
  <div class="chart-range-presets" role="group" aria-label="Chart period" data-testid="chart-range-presets">
    <button
      v-for="option in CHART_RANGE_PRESETS"
      :key="option.value"
      type="button"
      class="accent-toggle-btn angular-chart-chip chart-range-presets__button"
      :class="{ 'accent-toggle-btn--active angular-chart-chip--active': modelValue === option.value }"
      :aria-pressed="modelValue === option.value"
      @click="emit('update:modelValue', option.value)"
    >{{ option.label }}</button>
    <span v-if="modelValue === 'custom'" class="chart-range-presets__custom">Custom</span>
  </div>
</template>

<script setup>
import { CHART_RANGE_PRESETS } from '@/composables/useDateRange'

defineProps({ modelValue: { type: String, default: 'mtd' } })
const emit = defineEmits(['update:modelValue'])
</script>

<style scoped>
.chart-range-presets {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem;
}
.chart-range-presets__button { min-height: 2rem; padding: 0.3rem 0.55rem; font-size: 0.75rem; }
.chart-range-presets__custom { font-size: 0.75rem; color: var(--color-text-muted); }
</style>
