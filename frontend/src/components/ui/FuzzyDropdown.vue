<!--
  FuzzyDropdown.vue
  Multi-select dropdown with fuzzy search.
-->
<template>
  <div class="relative">
    <input v-model="query" type="text" :placeholder="placeholder" class="input w-full mb-2" @focus="open = true"
      @keydown.esc="open = false" @blur="onBlur" />
    <div v-show="open" class="dropdown-menu w-full">
      <label v-for="item in filtered" :key="item.id" class="flex items-center gap-2 py-1">
        <input type="checkbox" :value="item.id" v-model="localValue"
          :disabled="max > 0 && !localValue.includes(item.id) && localValue.length >= max" />
        <span>{{ item.name }}</span>
      </label>
      <p v-if="!filtered.length" class="text-sm text-[var(--color-text-muted)] py-2">No matches</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import Fuse from 'fuse.js'

const props = defineProps({
  options: { type: Array, default: () => [] }, // [{id, name}]
  modelValue: { type: Array, default: () => [] }, // Multi-select
  max: { type: Number, default: 0 }, // 0 = unlimited
  placeholder: { type: String, default: 'Search…' },
})
const emit = defineEmits(['update:modelValue'])

const query = ref('')
const open = ref(false)

// Safe copy for controlled multi-select
const safeModel = computed(() =>
  Array.isArray(props.modelValue) ? props.modelValue : []
)
const localValue = ref([...safeModel.value])

watch(
  () => props.modelValue,
  val => (localValue.value = [...(Array.isArray(val) ? val : [])])
)
watch(
  localValue,
  val => emit('update:modelValue', val),
  { deep: true }
)

const fuse = computed(() =>
  new Fuse(props.options, { keys: ['name'], threshold: 0.3 })
)
const filtered = computed(() => {
  if (!query.value) {
    return props.options.slice(0, props.max || 50)
  }
  return fuse.value.search(query.value).map(r => r.item)
})

// UX: close on blur unless clicking into dropdown
function onBlur() {
  setTimeout(() => {
    open.value = false
  }, 180)
}
</script>

<style scoped>
@reference "../../assets/css/main.css";
.dropdown-menu {
  @apply absolute bg-[var(--themed-bg)] border border-[var(--divider)] p-2 flex flex-col gap-1 max-h-48 overflow-y-auto z-10;
}
</style>
