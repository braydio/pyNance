<template>
  <div class="relative">
    <div class="dropdown-trigger input w-full mb-2 cursor-pointer flex items-center" @click="open = !open"
      @keydown.esc="open = false" tabindex="0">
      <span class="flex-1 truncate text-left">
        <template v-if="selectedNames.length">{{ selectedNames.join(', ') }}</template>
        <template v-else class="text-gray-400">{{ placeholder }}</template>
      </span>
      <span class="ml-2">&or;</span>
    </div>
    <div v-show="open" class="dropdown-menu w-full z-30" @mousedown.prevent>
      <div v-for="group in groups" :key="group.id" class="mb-1">
        <label class="flex items-center gap-2 py-1 font-bold">
          <input type="checkbox" :value="group.id" :checked="isGroupAllSelected(group)"
            :indeterminate.prop="isGroupIndeterminate(group)" @change="toggleGroup(group)" />
          <span>{{ group.label }}</span>
        </label>
        <div v-if="isGroupExpanded(group)" class="ml-7">
          <label v-for="child in group.children" :key="child.id" class="flex items-center gap-2 py-1">
            <input type="checkbox" :value="child.id" :checked="selectedIds.has(child.id)"
              @change="toggleChild(group, child)" />
            <span>{{ child.label }}</span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  groups: { type: Array, required: true },
  modelValue: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Select categories…' }
})
const emit = defineEmits(['update:modelValue'])
const open = ref(false)
const expanded = ref(new Set())
const selectedIds = ref(new Set(props.modelValue))

watch(
  () => props.modelValue,
  val => (selectedIds.value = new Set(val))
)
watch(
  selectedIds,
  val => emit('update:modelValue', Array.from(val)),
  { deep: true }
)

function toggleGroup(group) {
  const allChildIds = group.children.map(c => c.id)
  const allSelected = allChildIds.every(id => selectedIds.value.has(id))
  if (allSelected) {
    allChildIds.forEach(id => selectedIds.value.delete(id))
    expanded.value.delete(group.id)
  } else {
    allChildIds.forEach(id => selectedIds.value.add(id))
    expanded.value.add(group.id)
  }
}
function isGroupExpanded(group) {
  // Expand if at least one child is selected, or if explicitly expanded
  return expanded.value.has(group.id) || group.children.some(c => selectedIds.value.has(c.id))
}
function toggleChild(group, child) {
  if (selectedIds.value.has(child.id)) {
    selectedIds.value.delete(child.id)
  } else {
    selectedIds.value.add(child.id)
    expanded.value.add(group.id)
  }
}
function isGroupAllSelected(group) {
  return group.children.every(c => selectedIds.value.has(c.id)) && group.children.length > 0
}
function isGroupIndeterminate(group) {
  const sel = group.children.filter(c => selectedIds.value.has(c.id)).length
  return sel > 0 && sel < group.children.length
}
const selectedNames = computed(() => {
  const names = []
  for (const group of props.groups) {
    const sel = group.children.filter(c => selectedIds.value.has(c.id))
    if (sel.length === group.children.length && sel.length > 0) {
      names.push(group.label)
    } else {
      sel.forEach(c => names.push(`${group.label}: ${c.label}`))
    }
  }
  return names
})
</script>

<style scoped>
@reference "../../assets/css/main.css";
.dropdown-menu {
  @apply absolute bg-[var(--themed-bg)] border border-[var(--divider)] p-2 flex flex-col gap-1 max-h-80 overflow-y-auto z-30 min-w-[270px] shadow;
}
</style>
