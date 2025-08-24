<template>
  <div class="flex items-center gap-2">
    <input
      type="date"
      :value="startDate"
      @input="onStart($event.target.value)"
      class="date-picker px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)] focus:ring-2 focus:ring-[var(--color-accent-cyan)]"
    />
    <input
      type="date"
      :value="endDate"
      @input="onEnd($event.target.value)"
      class="date-picker px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)] focus:ring-2 focus:ring-[var(--color-accent-cyan)]"
    />
    <button
      v-if="!disableZoom"
      class="btn btn-outline hover-lift ml-2"
      @click="toggleZoom"
    >
      {{ zoomedOut ? 'Zoom In' : 'Zoom Out' }}
    </button>
  </div>
</template>

<script setup>
/**
 * DateRangeSelector
 * Provides start/end date inputs and a zoom toggle for switching
 * between detailed and aggregated chart views. The component also
 * ensures the start date never exceeds the end date by adjusting the
 * complementary bound when needed.
 */
import { toRefs } from 'vue'

const props = defineProps({
  startDate: { type: String, required: true },
  endDate: { type: String, required: true },
  zoomedOut: { type: Boolean, default: false },
  disableZoom: { type: Boolean, default: false },
})

const emit = defineEmits(['update:startDate', 'update:endDate', 'update:zoomedOut'])
const { startDate, endDate, zoomedOut, disableZoom } = toRefs(props)

function onStart(val) {
  if (endDate.value && val > endDate.value) {
    emit('update:endDate', val)
  }
  emit('update:startDate', val)
}
function onEnd(val) {
  if (startDate.value && val < startDate.value) {
    emit('update:startDate', val)
  }
  emit('update:endDate', val)
}
function toggleZoom() {
  if (disableZoom.value) return
  emit('update:zoomedOut', !zoomedOut.value)
}
</script>

<style scoped>
.date-picker {
  min-width: 10rem;
}
</style>
