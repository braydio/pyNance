<template>
  <div class="relative w-full">
    <div
      class="dropdown-trigger input w-full mb-2 cursor-pointer flex items-center px-3 py-2 rounded-lg border border-[var(--divider)] bg-[var(--color-bg-secondary)] shadow transition hover:border-[var(--color-accent-mint)] focus:border-[var(--color-accent-mint)]"
      @click="open = !open" @keydown.esc="open = false" tabindex="0" :aria-expanded="open" :aria-haspopup="true">
      <span class="flex-1 truncate text-left text-[var(--color-text-light)]">
        <template v-if="selectedNames.length">{{ selectedNames.join(', ') }}</template>
        <span v-else class="text-[var(--color-text-muted)] italic">{{ placeholder }}</span>
      </span>
      <span class="ml-2 transition-transform" :class="{ 'rotate-180': open }" style="font-size: 1.25em"
        aria-label="Dropdown">▼</span>
    </div>

    <transition name="fade">
      <div v-show="open"
        class="dropdown-menu w-full absolute left-0 mt-1 z-40 p-2 rounded-2xl border border-[var(--divider)] shadow-xl bg-[var(--color-bg-sec)] backdrop-blur-lg"
        @mousedown.prevent>
        <div v-for="group in groups" :key="group.id" class="mb-2 last:mb-0 group-block">
          <label
            class="flex items-center gap-2 py-1 font-semibold text-[var(--color-accent-ice)] tracking-tight rounded-lg hover:bg-[var(--color-bg-secondary)] cursor-pointer transition">
            <input type="checkbox" :value="group.id" :checked="isGroupAllSelected(group)"
              :indeterminate.prop="isGroupIndeterminate(group)" @change="toggleGroup(group)"
              class="accent-[var(--color-accent-mint)] w-4 h-4 rounded border border-[var(--divider)] shadow focus:ring-2 focus:ring-[var(--color-accent-mint)] transition" />
            <span>{{ group.label }}</span>
            <span
              class="ml-auto text-xs px-2 py-0.5 rounded bg-[var(--color-accent-mint)] bg-opacity-20 text-[var(--color-accent-mint)]"
              v-if="group.children.length">
              {{ group.children.length }}
            </span>
            <span v-if="isGroupExpanded(group)" class="ml-1 text-[var(--color-accent-mint)] text-base">▾</span>
            <span v-else class="ml-1 text-[var(--color-text-muted)] text-base">▸</span>
          </label>

          <transition name="slide">
            <div v-if="isGroupExpanded(group)" class="pl-8 py-1">
              <label v-for="child in group.children" :key="child.id"
                class="flex items-center gap-2 py-1 px-2 rounded-md hover:bg-[var(--color-bg-secondary)] cursor-pointer transition text-[var(--color-text-light)]">
                <input type="checkbox" :value="child.id" :checked="selectedIds.has(child.id)"
                  @change="toggleChild(group, child)"
                  class="accent-[var(--color-accent-yellow)] w-4 h-4 rounded border border-[var(--divider)] shadow" />
                <span>{{ child.label }}</span>
              </label>
            </div>
          </transition>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
// Multi-select dropdown for selecting categories grouped by parent.
// Emits `update:modelValue` with the selected category IDs.
import { ref, computed, watch } from 'vue'

const props = defineProps({
  groups: { type: Array, required: true },
  modelValue: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Select categories…' }
})
const emit = defineEmits(['update:modelValue'])
const open = ref(false)
const expanded = ref(new Set())
// Local copy of selected ids; kept in sync with the parent via v-model
const selectedIds = ref(new Set(props.modelValue))
// Flag prevents prop updates from triggering a feedback loop
const updatingFromProps = ref(false)

// When parent updates the modelValue, sync our local set
watch(
  () => props.modelValue,
  val => {
    updatingFromProps.value = true
    selectedIds.value = new Set(val)
  }
)
// Emit changes only when they originate from user interaction
watch(
  selectedIds,
  val => {
    if (updatingFromProps.value) {
      updatingFromProps.value = false
      return
    }
    emit('update:modelValue', Array.from(val))
  },
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
@import "../../assets/css/main.css";

.dropdown-menu {
  background: var(--color-bg-sec, #181924);
  box-shadow: 0 8px 32px 0 rgb(24 25 36 / 48%), 0 1.5px 6px 0 rgb(56 255 212 / 8%);
  border-radius: 1.2rem;
  min-width: 260px;
  max-width: 95vw;
  padding: 1rem;
  border: 1.5px solid var(--divider, #303049);
  /* backdrop-filter: blur(10px); */
}

.group-block+.group-block {
  border-top: 1px solid var(--divider, #232343);
  margin-top: 0.5rem;
  padding-top: 0.5rem;
}

input[type="checkbox"] {
  outline: none;
  accent-color: var(--color-accent-mint, #38ffd4);
  transition: box-shadow 0.2s;
}

input[type="checkbox"]:focus-visible {
  box-shadow: 0 0 0 2px var(--color-accent-mint, #38ffd4);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: max-height 0.24s cubic-bezier(.61, 1, .88, 1), opacity 0.17s;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
