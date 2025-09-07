<template>
  <div class="relative w-full" v-click-outside="close">
    <!-- Trigger -->
    <div
      class="dropdown-trigger input w-full mb-2 cursor-pointer flex items-center px-3 py-2 rounded-lg border border-[var(--divider)] bg-[var(--color-bg-secondary)] shadow transition hover:border-[var(--color-accent-cyan)] focus:border-[var(--color-accent-cyan)]"
      @click="open = !open"
      @keydown.esc="open = false"
      tabindex="0"
      :aria-expanded="open"
      :aria-haspopup="true"
    >
      <span class="flex-1 truncate text-left text-[var(--color-text-light)]">
        <span class="text-[var(--color-text-muted)] italic">{{ placeholder }}</span>
      </span>
      <span
        class="ml-2 transition-transform"
        :class="{ 'rotate-180': open }"
        style="font-size: 1.25em"
        aria-label="Dropdown"
        >▼</span
      >
    </div>

    <!-- Dropdown menu -->
    <transition name="fade">
      <div
        v-show="open"
        class="dropdown-menu w-full absolute left-0 mt-1 z-40 p-2 rounded-2xl border border-[var(--divider)] shadow-xl bg-[var(--color-bg-sec)] backdrop-blur-lg"
        @mousedown.prevent
      >
        <div v-for="(group, idx) in groups" :key="group.id" class="mb-2 last:mb-0 group-block">
          <label
            class="flex items-center gap-2 py-1 font-semibold text-[var(--color-accent-cyan)] tracking-tight rounded-lg hover:bg-[var(--color-bg-secondary)] cursor-pointer transition"
          >
            <!-- Color dot for group -->
            <span
              class="inline-block w-3 h-3 rounded-full border border-[var(--divider)] shadow-sm"
              :style="`background: ${groupDotColor(idx)}`"
              aria-hidden="true"
            ></span>
            <input
              type="checkbox"
              :checked="isGroupAllSelected(group)"
              :indeterminate.prop="isGroupIndeterminate(group)"
              @change="toggleGroup(group)"
              class="accent-[var(--color-accent-cyan)] w-4 h-4 rounded border border-[var(--divider)] shadow focus:ring-2 focus:ring-[var(--color-accent-cyan)] transition"
            />
            <span>{{ group.label }}</span>
            <span
              class="ml-auto text-xs px-2 py-0.5 rounded bg-[var(--color-accent-cyan)] bg-opacity-20 text-[var(--color-accent-cyan)]"
              v-if="group.children.length"
            >
              {{ group.children.length }}
            </span>
            <span
              v-if="isGroupExpanded(group)"
              class="ml-1 text-[var(--color-accent-cyan)] text-base"
              >▾</span
            >
            <span v-else class="ml-1 text-[var(--color-text-muted)] text-base">▸</span>
          </label>
          <transition name="slide">
            <div v-if="isGroupExpanded(group)" class="pl-8 py-1">
              <label
                v-for="child in group.children"
                :key="child.id"
                class="flex items-center gap-2 py-1 px-2 rounded-md hover:bg-[var(--color-bg-secondary)] cursor-pointer transition text-[var(--color-text-light)]"
              >
                <input
                  type="checkbox"
                  :checked="selectedIds.has(child.id)"
                  @change="toggleChild(group, child)"
                  class="accent-[var(--color-accent-yellow)] w-4 h-4 rounded border border-[var(--divider)] shadow"
                />
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
import { ref, watch } from 'vue'

const props = defineProps({
  groups: { type: Array, required: true },
  modelValue: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Select categories…' },
})
const emit = defineEmits(['update:modelValue'])
const open = ref(false)
const expanded = ref(new Set())
// Normalize to strings so comparisons with API results are consistent
const selectedIds = ref(new Set((props.modelValue || []).map((x) => String(x))))
const updatingFromProps = ref(false)

// Rainbow dot palette for groups
const groupDotPalette = [
  '#a78bfa',
  '#5db073',
  '#fbbf24',
  '#a43e5c',
  '#3b82f6',
  '#eab308',
  '#f472b6',
  '#60a5fa',
  '#e11d48',
  '#38ffd4',
  '#8B5CF6',
  '#22D3EE',
  '#FDA4AF',
  '#FCD34D',
  '#34D399',
]
function groupDotColor(idx) {
  return groupDotPalette[idx % groupDotPalette.length]
}

watch(
  () => props.modelValue,
  (val) => {
    updatingFromProps.value = true
    selectedIds.value = new Set((val || []).map((x) => String(x)))
  },
)
watch(
  selectedIds,
  (val) => {
    if (updatingFromProps.value) {
      updatingFromProps.value = false
      return
    }
    emit('update:modelValue', Array.from(val))
  },
  { deep: true },
)

function toggleGroup(group) {
  const allChildIds = group.children.map((c) => String(c.id))
  const allSelected = allChildIds.every((id) => selectedIds.value.has(id))
  if (allSelected) {
    // Remove all children (must create new Set)
    selectedIds.value = new Set([...selectedIds.value].filter((id) => !allChildIds.includes(id)))
    expanded.value = new Set([...expanded.value].filter((id) => id !== group.id))
  } else {
    // Add all children
    selectedIds.value = new Set([...selectedIds.value, ...allChildIds])
    expanded.value = new Set(expanded.value).add(group.id)
  }
}
function isGroupExpanded(group) {
  return (
    expanded.value.has(group.id) || group.children.some((c) => selectedIds.value.has(String(c.id)))
  )
}
function toggleChild(group, child) {
  const cid = String(child.id)
  if (selectedIds.value.has(cid)) {
    selectedIds.value = new Set([...selectedIds.value].filter((id) => id !== cid))
  } else {
    selectedIds.value = new Set([...selectedIds.value, cid])
    expanded.value = new Set(expanded.value).add(group.id)
  }
}
function isGroupAllSelected(group) {
  return (
    group.children.length > 0 && group.children.every((c) => selectedIds.value.has(String(c.id)))
  )
}
function isGroupIndeterminate(group) {
  const sel = group.children.filter((c) => selectedIds.value.has(String(c.id))).length
  return sel > 0 && sel < group.children.length
}

function close() {
  open.value = false
}
</script>
