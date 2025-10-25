<template>
  <BasePageLayout>
    <slot name="header" />
    <div class="flex gap-8">
      <div class="flex-1">
        <nav class="tabbed-nav" data-testid="tabbed-nav">
          <ul class="tabbed-nav__list">
            <li v-for="tab in tabs" :key="tab">
              <UiButton
                :variant="activeTab === tab ? 'primary' : 'outline'"
                :pill="true"
                class="tabbed-nav__button"
                @click="selectTab(tab)"
              >
                {{ tab }}
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
 * - tabs: array of tab labels displayed in navigation
 * - modelValue: currently active tab (used with v-model)
 */
import { computed } from 'vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import UiButton from '@/components/ui/Button.vue'

const props = defineProps({
  /** Array of tab labels */
  tabs: { type: Array, default: () => [] },
  /** Currently selected tab */
  modelValue: { type: String, default: '' },
  /** Optional width utility class for sidebar (e.g. 'w-72 md:w-80') */
  sidebarWidth: { type: String, default: 'w-64' },
})

const emit = defineEmits(['update:modelValue'])

const activeTab = computed({
  get: () => props.modelValue || props.tabs[0],
  set: (val) => emit('update:modelValue', val),
})

function selectTab(tab) {
  activeTab.value = tab
}

const sidebarWidthClass = computed(() => props.sidebarWidth || 'w-64')
</script>

<style scoped>
.tabbed-nav {
  margin-bottom: 1.5rem;
  padding: 0.75rem 1rem;
  border-radius: 999px;
  border: 1px solid rgba(113, 156, 214, 0.35);
  background:
    linear-gradient(
      135deg,
      rgba(99, 205, 207, 0.08) 0%,
      rgba(113, 156, 214, 0.12) 50%,
      rgba(214, 122, 210, 0.08) 100%
    ),
    rgba(19, 24, 44, 0.65);
  box-shadow: 0 18px 40px rgba(12, 17, 35, 0.45);
  backdrop-filter: blur(8px);
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
  border-radius: 999px;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease,
    border-color 0.2s ease;
}

.tabbed-nav__button:hover {
  transform: translateY(-2px);
}

.tabbed-nav__button.btn-outline {
  background: rgba(17, 23, 42, 0.35);
  color: var(--color-accent-purple);
  border-color: rgba(113, 156, 214, 0.4);
  box-shadow: inset 0 0 0 1px rgba(113, 156, 214, 0.25);
}

.tabbed-nav__button.btn-outline:hover {
  background: rgba(113, 156, 214, 0.18);
  border-color: rgba(113, 156, 214, 0.6);
  box-shadow: inset 0 0 0 1px rgba(214, 122, 210, 0.35);
}

.tabbed-nav__button.btn-primary {
  background: linear-gradient(
    135deg,
    rgba(99, 205, 207, 0.95) 0%,
    rgba(113, 156, 214, 0.95) 50%,
    rgba(214, 122, 210, 0.95) 100%
  );
  border-color: transparent;
  color: var(--color-bg-dark);
  box-shadow: 0 12px 28px rgba(99, 205, 207, 0.32);
}

.tabbed-nav__button.btn-primary:hover {
  box-shadow: 0 16px 34px rgba(99, 205, 207, 0.42);
}

@media (max-width: 768px) {
  .tabbed-nav {
    border-radius: 1.25rem;
  }

  .tabbed-nav__list {
    justify-content: center;
  }
}
</style>
