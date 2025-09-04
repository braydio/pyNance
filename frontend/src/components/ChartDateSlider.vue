<template>
  <div class="date-slider">
    <div class="labels">
      <span class="label">{{ formatDate(displayStart) }}</span>
      <span class="label">{{ formatDate(displayEnd) }}</span>
    </div>
    <div class="sliders">
      <input type="range" :min="0" :max="maxIdx" v-model.number="startIdx" @input="onStartIdx" />
      <input type="range" :min="0" :max="maxIdx" v-model.number="endIdx" @input="onEndIdx" />
    </div>
    <div class="ticks" aria-hidden="true">
      <span v-for="t in tickMarks" :key="t.index" class="tick" :style="{ left: t.left }">{{ t.label }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  // Selection (linked with parent)
  startDate: { type: String, required: true },
  endDate: { type: String, required: true },
  // Stable domain for the slider (should not change as the selection changes)
  domainStart: { type: String, required: true },
  domainEnd: { type: String, required: true },
})
const emit = defineEmits(['update:startDate', 'update:endDate'])

function formatDate(s) {
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return s
  return d.toLocaleDateString(undefined, { month: 'short', day: '2-digit', year: '2-digit' })
}

// Build a date array from start..end (inclusive)
const dateList = computed(() => {
  const out = []
  try {
    const s = new Date(props.domainStart)
    const e = new Date(props.domainEnd)
    if (Number.isNaN(s) || Number.isNaN(e) || s > e) return out
    const d = new Date(s)
    while (d <= e && out.length < 1000) {
      out.push(d.toISOString().slice(0, 10))
      d.setDate(d.getDate() + 1)
    }
  } catch {}
  return out
})

const maxIdx = computed(() => Math.max(0, dateList.value.length - 1))
const startIdx = ref(0)
const endIdx = ref(0)

const displayStart = computed(() => dateList.value[startIdx.value] || props.startDate)
const displayEnd = computed(() => dateList.value[endIdx.value] || props.endDate)

// Keep slider thumbs synced to the selection within the domain
function syncThumbsToSelection() {
  const list = dateList.value
  if (!list.length) return
  const sIdx = Math.max(0, list.indexOf(props.startDate))
  const eIdx = Math.max(0, list.indexOf(props.endDate))
  startIdx.value = sIdx >= 0 ? sIdx : 0
  endIdx.value = eIdx >= 0 ? eIdx : list.length - 1
  if (startIdx.value > endIdx.value) startIdx.value = Math.min(endIdx.value, startIdx.value)
}

watch(() => [props.domainStart, props.domainEnd], () => syncThumbsToSelection(), { immediate: true })
watch(() => [props.startDate, props.endDate], () => syncThumbsToSelection())

function onStartIdx() {
  if (startIdx.value > endIdx.value) endIdx.value = startIdx.value
  const s = dateList.value[startIdx.value]
  if (s) emit('update:startDate', s)
}
function onEndIdx() {
  if (endIdx.value < startIdx.value) startIdx.value = endIdx.value
  const e = dateList.value[endIdx.value]
  if (e) emit('update:endDate', e)
}

const tickMarks = computed(() => {
  const list = dateList.value
  if (!list.length) return []
  const step = Math.max(1, Math.floor(list.length / 4))
  return list
    .map((d, i) => (i % step === 0 ? { index: i, date: d } : null))
    .filter(Boolean)
    .map((t) => ({
      index: t.index,
      left: `${(t.index / Math.max(1, list.length - 1)) * 100}%`,
      label: new Date(t.date).toLocaleDateString(undefined, { month: 'short' }),
    }))
})
</script>

<style scoped>
.date-slider { position: relative; padding-top: .25rem; }
.labels { display: flex; justify-content: space-between; font-size: .85rem; color: var(--color-text-muted); margin-bottom: .25rem; }
.sliders { position: relative; height: 1.75rem; }
.sliders input[type="range"] { position: absolute; left: 0; right: 0; width: 100%; -webkit-appearance: none; background: none; }
.sliders input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; width: 14px; height: 14px; border-radius: 50%; background: var(--color-accent-cyan); border: 2px solid var(--theme-bg); }
.sliders input[type="range"]::-moz-range-thumb { width: 14px; height: 14px; border-radius: 50%; background: var(--color-accent-cyan); border: 2px solid var(--theme-bg); }
.ticks { position: relative; height: .75rem; }
.tick { position: absolute; transform: translateX(-50%); font-size: .7rem; color: var(--color-text-muted); }
.label { font-variant-numeric: tabular-nums; }
</style>
