<template>
  <div class="chart-controls">
    <label><input type="checkbox" :checked="show7Day" @change="emit('update:show7Day', $event.target.checked)" /> 7d trend</label>
    <label><input type="checkbox" :checked="show30Day" @change="emit('update:show30Day', $event.target.checked)" /> 30d trend</label>
    <label><input type="checkbox" :checked="showAvgIncome" @change="emit('update:showAvgIncome', $event.target.checked)" /> AVERAGE SHIT-NCOME</label>
    <label><input type="checkbox" :checked="showAvgExpenses" @change="emit('update:showAvgExpenses', $event.target.checked)" /> avg expenses</label>
  </div>
</template>

<script setup>
/**
 * Checkbox controls for toggling trend and average lines on charts.
 */
import { toRefs } from 'vue'

const props = defineProps({
  show7Day: { type: Boolean, default: false },
  show30Day: { type: Boolean, default: false },
  showAvgIncome: { type: Boolean, default: false },
  showAvgExpenses: { type: Boolean, default: false }
})
const emit = defineEmits(['update:show7Day', 'update:show30Day', 'update:showAvgIncome', 'update:showAvgExpenses'])
const { show7Day, show30Day, showAvgIncome, showAvgExpenses } = toRefs(props)
</script>

<style scoped>
.chart-controls {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.chart-controls label {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
</style>

