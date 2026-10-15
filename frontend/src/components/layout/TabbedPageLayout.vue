<template>
  <BasePageLayout>
    <slot name="header" />
    <div class="flex flex-col gap-8 lg:flex-row">
      <div class="min-w-0 flex-1">
        <nav
          class="tabbed-nav ui-radius-3 border border-subtle bg-surface-2"
          data-testid="tabbed-nav"
        >
          <ul
            ref="tabListRef"
            class="tabbed-nav__list"
            :class="{
              'tabbed-nav__list--fade-start': canScrollStart,
              'tabbed-nav__list--fade-end': canScrollEnd,
            }"
            role="tablist"
            aria-label="Page sections"
            @scroll.passive="updateScrollState"
          >
            <li v-for="tab in normalizedTabs" :key="tab.slot" role="presentation">
              <UiButton
                :id="`tab-${tab.slot}`"
                role="tab"
                :aria-selected="activeTab === tab.slot"
                :aria-controls="`tabpanel-${tab.slot}`"
                :tabindex="activeTab === tab.slot ? 0 : -1"
                @keydown="onTabKeydown($event, tab.slot)"
                :variant="activeTab === tab.slot ? 'primary' : 'outline'"
                :pill="false"
                class="tabbed-nav__button ui-radius-2"
                :disabled="tab.disabled"
                @click="selectTab(tab.slot)"
              >
                {{ tab.label }}
              </UiButton>
            </li>
          </ul>
        </nav>
        <div :id="`tabpanel-${activeTab}`" role="tabpanel" :aria-labelledby="`tab-${activeTab}`">
          <slot :name="activeTab" />
        </div>
      </div>
      <aside
        v-if="$slots.sidebar"
        :class="[sidebarWidthClass, 'max-lg:w-full min-w-0 flex-shrink-0 relative']"
        data-testid="tabbed-sidebar"
      >
        <!-- Ensure sidebar actions stay clickable above main content -->
        <slot name="sidebar" />
      </aside>
    </div>
  </BasePageLayout>
</template>

<script setup>
/**
 * TabbedPageLayout
 * Layout component providing a header slot, tab navigation, and optional sidebar.
 * Tab navigation buttons use the shared UiButton component for consistent theming.
 *
 * Props:
 * - tabs: array of tab labels or objects ({ label, slot }) displayed in navigation
 *   with optional `disabled` state ({ label, slot, disabled })
 * - modelValue: currently active tab (used with v-model)
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import UiButton from '@/components/ui/Button.vue'

const props = defineProps({
  /** Array of tab labels or objects ({ label, slot }) */
  tabs: { type: Array, default: () => [] },
  /** Currently selected tab */
  modelValue: { type: String, default: '' },
  /** Optional width utility class for sidebar (e.g. 'w-72 md:w-80') */
  sidebarWidth: { type: String, default: 'w-64' },
})

const emit = defineEmits(['update:modelValue'])

/**
 * Normalize any provided tab definitions into a shared object shape so the
 * layout can support both simple string labels and explicit slot mappings,
 * including optional disabled state per tab.
 */
const normalizedTabs = computed(() =>
  props.tabs.map((tab) =>
    typeof tab === 'string'
      ? { label: tab, slot: tab, disabled: false }
      : {
          label: tab.label ?? tab.slot ?? '',
          slot: tab.slot ?? tab.label ?? '',
          disabled: Boolean(tab.disabled),
        },
  ),
)

const activeTab = computed({
  get: () => props.modelValue || normalizedTabs.value[0]?.slot || '',
  set: (val) => emit('update:modelValue', val),
})

function selectTab(tabSlot) {
  const tab = normalizedTabs.value.find((candidate) => candidate.slot === tabSlot)
  if (tab?.disabled) {
    return
  }
  activeTab.value = tabSlot
}

/**
 * Arrow/Home/End keyboard navigation between enabled tabs (roving tabindex).
 *
 * @param {KeyboardEvent} event
 * @param {string} tabSlot - Slot of the tab that received the key event.
 */
function onTabKeydown(event, tabSlot) {
  const keys = ['ArrowLeft', 'ArrowRight', 'Home', 'End']
  if (!keys.includes(event.key)) return
  const enabled = normalizedTabs.value.filter((tab) => !tab.disabled)
  const index = enabled.findIndex((tab) => tab.slot === tabSlot)
  if (index === -1) return
  event.preventDefault()
  let next = index
  if (event.key === 'ArrowRight') next = (index + 1) % enabled.length
  if (event.key === 'ArrowLeft') next = (index - 1 + enabled.length) % enabled.length
  if (event.key === 'Home') next = 0
  if (event.key === 'End') next = enabled.length - 1
  selectTab(enabled[next].slot)
  document.getElementById(`tab-${enabled[next].slot}`)?.focus()
}

const sidebarWidthClass = computed(() => props.sidebarWidth || 'w-64')

// Narrow screens: one scrollable row with edge fades and the active tab kept in view.
const tabListRef = ref(null)
const canScrollStart = ref(false)
const canScrollEnd = ref(false)

function updateScrollState() {
  const el = tabListRef.value
  if (!el) return
  const max = el.scrollWidth - el.clientWidth
  canScrollStart.value = el.scrollLeft > 1
  canScrollEnd.value = max > 1 && el.scrollLeft < max - 1
}

async function revealActiveTab() {
  await nextTick()
  document
    .getElementById(`tab-${activeTab.value}`)
    ?.scrollIntoView?.({ inline: 'center', block: 'nearest' })
  updateScrollState()
}

onMounted(() => {
  updateScrollState()
  window.addEventListener('resize', updateScrollState)
})
onBeforeUnmount(() => window.removeEventListener('resize', updateScrollState))
watch(activeTab, revealActiveTab)
</script>

<style scoped>
.tabbed-nav {
  margin-bottom: 1.5rem;
  padding: 0.75rem 1rem;
  box-shadow: var(--depth-inner-glow), var(--depth-shadow-resting);
}

.tabbed-nav__list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: flex-start;
}

.tabbed-nav__button {
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  padding: 0.55rem 1.35rem;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.tabbed-nav__button:hover {
  transform: translateY(-2px);
}

.tabbed-nav__button.btn-primary {
  box-shadow: var(--depth-shadow-raised);
}

@media (max-width: 768px) {
  .tabbed-nav {
    padding: 0.5rem 0.75rem;
  }

  .tabbed-nav__list {
    flex-wrap: nowrap;
    overflow-x: auto;
    gap: 0.5rem;
    scrollbar-width: none;
    scroll-snap-type: x proximity;
    scroll-padding-inline: 1.5rem;
  }

  .tabbed-nav__list::-webkit-scrollbar {
    display: none;
  }

  .tabbed-nav__list > li {
    flex: 0 0 auto;
    scroll-snap-align: center;
  }

  .tabbed-nav__button {
    padding: 0.5rem 1rem;
    white-space: nowrap;
  }

  .tabbed-nav__list--fade-end {
    mask-image: linear-gradient(to right, #000 calc(100% - 1.75rem), transparent);
  }

  .tabbed-nav__list--fade-start {
    mask-image: linear-gradient(to right, transparent, #000 1.75rem);
  }

  .tabbed-nav__list--fade-start.tabbed-nav__list--fade-end {
    mask-image: linear-gradient(
      to right,
      transparent,
      #000 1.75rem,
      #000 calc(100% - 1.75rem),
      transparent
    );
  }
}

@media (prefers-reduced-motion: reduce) {
  .tabbed-nav__button {
    transition: none;
  }

  .tabbed-nav__button:hover {
    transform: none;
  }
}
</style>
