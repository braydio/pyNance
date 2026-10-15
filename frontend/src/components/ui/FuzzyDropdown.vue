<!--
  FuzzyDropdown.vue
  Multi-select dropdown with fuzzy search. Stays open while focus is inside it and closes on
  focus leaving, Escape or an outside click (no blur timers).
-->
<template>
  <div ref="rootRef" class="relative" v-click-outside="close" @focusout="onFocusOut">
    <input
      v-model="query"
      type="text"
      role="combobox"
      :placeholder="placeholder"
      :aria-label="label || placeholder"
      :aria-expanded="open ? 'true' : 'false'"
      :aria-controls="menuId"
      aria-autocomplete="list"
      class="input w-full mb-2"
      @focus="open = true"
      @keydown.esc="onEscape"
      @keydown.down.prevent="open = true"
    />
    <div
      v-show="open"
      :id="menuId"
      class="dropdown-menu w-full"
      role="group"
      :aria-label="label || placeholder"
    >
      <label v-for="item in filtered" :key="item.id" class="flex items-center gap-2 py-1">
        <input
          type="checkbox"
          :value="item.id"
          v-model="localValue"
          :disabled="atMax && !localValue.includes(item.id)"
        />
        <span>{{ item.name }}</span>
      </label>
      <p v-if="!filtered.length" class="text-sm text-muted py-2">No matches</p>
      <p v-if="atMax" class="text-sm text-muted py-1" role="status" data-testid="fuzzy-max-note">
        Maximum of {{ max }} selected. Remove one to choose another.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, useId } from 'vue'
import Fuse from 'fuse.js'

const props = defineProps({
  options: { type: Array, default: () => [] }, // [{id, name}]
  modelValue: { type: Array, default: () => [] }, // Multi-select
  max: { type: Number, default: 0 }, // 0 = unlimited
  placeholder: { type: String, default: 'Search…' },
  /** Accessible name for the search field and list (defaults to the placeholder). */
  label: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const query = ref('')
const open = ref(false)
const rootRef = ref(null)
const menuId = `fuzzy-dropdown-${useId()}`

// Safe copy for controlled multi-select
const safeModel = computed(() => (Array.isArray(props.modelValue) ? props.modelValue : []))
const localValue = ref([...safeModel.value])

watch(
  () => props.modelValue,
  (val) => (localValue.value = [...(Array.isArray(val) ? val : [])]),
)
watch(localValue, (val) => emit('update:modelValue', val), { deep: true })

const atMax = computed(() => props.max > 0 && localValue.value.length >= props.max)

const fuse = computed(() => new Fuse(props.options, { keys: ['name'], threshold: 0.3 }))
const filtered = computed(() => {
  if (!query.value) {
    // `max` limits how many can be selected, not how many options are listed.
    return props.options.slice(0, 50)
  }
  return fuse.value.search(query.value).map((r) => r.item)
})

/** Close only when focus moves outside the component; clicks inside keep focus-within. */
function onFocusOut(event) {
  const next = event.relatedTarget
  if (next && rootRef.value?.contains(next)) return
  // A click on a non-focusable area inside the menu reports relatedTarget === null; the
  // outside-click directive handles real outside clicks.
  if (!next) return
  open.value = false
}

function onEscape() {
  open.value = false
}

function close() {
  open.value = false
}
</script>

<style scoped>
@reference "../../assets/css/main.css";
.dropdown-menu {
  @apply absolute bg-[var(--themed-bg)] border border-[var(--divider)] p-2 flex flex-col gap-1 overflow-y-auto z-10;
  max-height: min(12rem, 40dvh);
}
</style>
