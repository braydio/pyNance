<template>
  <div class="relative w-full" v-click-outside="close" @keydown.esc.stop="onEscape">
    <!-- Trigger: a real button so Enter/Space and focus work natively -->
    <button
      ref="triggerRef"
      type="button"
      class="dropdown-trigger input w-full mb-2 cursor-pointer flex items-center rounded-lg shadow transition"
      :aria-expanded="open ? 'true' : 'false'"
      :aria-controls="menuId"
      aria-haspopup="true"
      @click="open = !open"
    >
      <span class="flex-1 truncate text-left text-[var(--color-text-light)]">
        <span v-if="selectedCount" data-testid="dropdown-selected-count">
          {{ selectedCount }} selected
        </span>
        <span v-else class="text-[var(--color-text-muted)] italic">{{ placeholder }}</span>
      </span>
      <span
        class="ml-2 transition-transform"
        :class="{ 'rotate-180': open }"
        style="font-size: 1.25em"
        aria-hidden="true"
        >▼</span
      >
    </button>

    <!-- Dropdown menu: bounded height, scrolls internally, never wider than the viewport -->
    <transition name="fade">
      <div
        v-show="open"
        :id="menuId"
        class="dropdown-menu w-full absolute left-0 mt-1 z-40 p-2 rounded-2xl border border-[var(--divider)] shadow-xl bg-[var(--color-bg-sec)] backdrop-blur-lg"
        role="group"
        aria-label="Category selection"
      >
        <div v-for="(group, idx) in groups" :key="group.id" class="mb-2 last:mb-0 group-block">
          <div class="flex items-center gap-1">
            <button
              type="button"
              class="group-expand-btn"
              :aria-expanded="isGroupExpanded(group) ? 'true' : 'false'"
              :aria-controls="`${menuId}-${group.id}`"
              :aria-label="`${isGroupExpanded(group) ? 'Collapse' : 'Expand'} ${group.label}`"
              @click="toggleExpanded(group)"
            >
              <span aria-hidden="true">{{ isGroupExpanded(group) ? '▾' : '▸' }}</span>
            </button>
            <label
              class="flex flex-1 items-center gap-2 py-1 font-semibold text-[var(--text-link)] tracking-tight rounded-lg hover:bg-[var(--color-bg-secondary)] cursor-pointer transition"
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
                class="ml-auto text-sm px-2 py-0.5 rounded text-[var(--text-link)]"
                v-if="group.children.length"
              >
                {{ group.children.length }}
              </span>
            </label>
          </div>
          <transition name="slide">
            <div v-if="isGroupExpanded(group)" :id="`${menuId}-${group.id}`" class="pl-8 py-1">
              <label
                v-for="child in group.children"
                :key="child.id"
                class="flex items-center gap-2 py-1 px-2 rounded-md hover:bg-[var(--color-bg-secondary)] cursor-pointer transition text-[var(--color-text-light)]"
              >
                <input
                  type="checkbox"
                  :checked="selectedIds.has(String(child.id))"
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
import { computed, ref, useId, watch } from 'vue'

const props = defineProps({
  groups: { type: Array, required: true },
  modelValue: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Select categories…' },
})
const emit = defineEmits(['update:modelValue'])
const open = ref(false)
const triggerRef = ref(null)
const menuId = `grouped-dropdown-${useId()}`
// Expansion is independent of selection; groups with selections start expanded.
const expanded = ref(new Set())
const expansionSeeded = ref(false)
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

const selectedCount = computed(() => selectedIds.value.size)

watch(
  () => props.groups,
  (groups) => {
    if (expansionSeeded.value || !groups?.length) return
    expansionSeeded.value = true
    expanded.value = new Set(
      groups
        .filter((group) => group.children.some((c) => selectedIds.value.has(String(c.id))))
        .map((group) => group.id),
    )
  },
  { immediate: true },
)

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
  } else {
    // Add all children
    selectedIds.value = new Set([...selectedIds.value, ...allChildIds])
  }
}
function isGroupExpanded(group) {
  return expanded.value.has(group.id)
}
function toggleExpanded(group) {
  const next = new Set(expanded.value)
  if (next.has(group.id)) next.delete(group.id)
  else next.add(group.id)
  expanded.value = next
}
function toggleChild(group, child) {
  const cid = String(child.id)
  if (selectedIds.value.has(cid)) {
    selectedIds.value = new Set([...selectedIds.value].filter((id) => id !== cid))
  } else {
    selectedIds.value = new Set([...selectedIds.value, cid])
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

/** Escape closes the menu and returns focus to the trigger. */
function onEscape() {
  if (!open.value) return
  open.value = false
  triggerRef.value?.focus?.()
}
</script>

<style scoped>
.dropdown-trigger {
  justify-content: space-between;
  text-align: left;
}

.dropdown-menu {
  max-height: min(20rem, 50dvh);
  overflow-y: auto;
  max-width: calc(100vw - 1rem);
  overscroll-behavior: contain;
}

.group-expand-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  min-height: 2rem;
  border-radius: 0.375rem;
  color: var(--text-muted);
}

.group-expand-btn:hover {
  background: var(--color-bg-secondary);
}

.group-expand-btn:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 1px;
}

@media (prefers-reduced-motion: reduce) {
  .dropdown-trigger span,
  .fade-enter-active,
  .fade-leave-active,
  .slide-enter-active,
  .slide-leave-active {
    transition: none;
  }
}
</style>
