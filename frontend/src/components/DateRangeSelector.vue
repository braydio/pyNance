<template>
  <div class="date-range-selector">
    <label class="date-field">
      <span class="date-field__label">From</span>
      <input
        type="date"
        :value="startDate"
        @input="onStart($event.target.value)"
        class="input date-picker"
      />
    </label>
    <label class="date-field">
      <span class="date-field__label">Through</span>
      <input
        type="date"
        :value="endDate"
        @input="onEnd($event.target.value)"
        class="input date-picker"
      />
    </label>
    <button
      v-if="!disableZoom"
      type="button"
      class="accent-toggle-btn date-range-selector__zoom"
      :class="{ 'accent-toggle-btn--active': zoomedOut }"
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
.date-range-selector {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.5rem;
  max-width: 100%;
  min-width: 0;
}

.date-field {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
  flex: 1 1 9rem;
}

.date-field__label {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.date-picker {
  min-width: 0;
  width: 100%;
}

.date-range-selector__zoom {
  min-height: var(--control-height);
}
</style>
