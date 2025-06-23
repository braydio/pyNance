<template>
  <div class="relative">
    <input
      v-model="query"
      type="text"
      placeholder="Search accounts..."
      class="input w-full mb-2"
      @focus="open = true"
    />
    <div v-show="open" class="dropdown-menu w-full">
      <label
        v-for="item in filtered"
        :key="item.account_id"
        class="flex items-center gap-2 py-1"
      >
        <input
          type="checkbox"
          :value="item.account_id"
          v-model="localValue"
          :disabled="!localValue.includes(item.account_id) && localValue.length >= max"
        />
        <span>{{ item.institution_name || item.name }}</span>
      </label>
      <p v-if="!filtered.length" class="text-sm text-gray-500 py-2">No matches</p>
    </div>
  </div>
</template>

<script setup>
/**
 * Fuzzy search dropdown for selecting account ids.
 * Options should be objects with `account_id`, `name`, and `institution_name` fields.
 */
import { ref, computed, watch } from 'vue'
import Fuse from 'fuse.js'

const props = defineProps({
  options: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
  max: { type: Number, default: 5 },
})
const emit = defineEmits(['update:modelValue'])

const query = ref('')
const open = ref(false)
const localValue = ref([...props.modelValue])

watch(
  () => props.modelValue,
  val => (localValue.value = [...val])
)
watch(
  localValue,
  val => emit('update:modelValue', val),
  { deep: true }
)

const fuse = computed(
  () =>
    new Fuse(props.options, { keys: ['name', 'institution_name'], threshold: 0.3 })
)

const filtered = computed(() => {
  if (!query.value) {
    return props.options.slice(0, props.max)
  }
  return fuse.value.search(query.value).map(r => r.item)
})
</script>

<style scoped>
.dropdown-menu {
  @apply absolute bg-[var(--themed-bg)] border border-[var(--divider)] p-2 flex flex-col gap-1 max-h-48 overflow-y-auto z-10;
}
</style>
