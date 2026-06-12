<template>
  <BasePageLayout>
    <slot name="header" />
    <div class="flex gap-8">
      <div class="flex-1">
        <nav class="tabbed-nav ui-radius-3 border border-subtle bg-surface-2" data-testid="tabbed-nav">
          <ul class="tabbed-nav__list">
            <li v-for="tab in normalizedTabs" :key="tab.slot">
              <UiButton
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
        <slot :name="activeTab" />
      </div>
      <aside v-if="$slots.sidebar" :class="[sidebarWidthClass, 'flex-shrink-0 relative z-10']">
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
import { computed } from 'vue'
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

const sidebarWidthClass = computed(() => props.sidebarWidth || 'w-64')
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
  .tabbed-nav__list {
    justify-content: center;
  }
}
</style>
