<template>
  <BasePageLayout>
    <slot name="header" />
    <div class="flex gap-8">
      <div class="flex-1">
        <nav class="border-b mb-4" data-testid="tabbed-nav">
          <ul class="flex gap-4">
            <li v-for="tab in tabs" :key="tab">
              <button
                class="pb-2 border-b-2"
                :class="
                  activeTab === tab
                    ? 'border-primary text-primary'
                    : 'border-transparent hover:border-muted'
                "
                @click="selectTab(tab)"
              >
                {{ tab }}
              </button>
            </li>
          </ul>
        </nav>
        <slot :name="activeTab" />
      </div>
      <aside v-if="$slots.sidebar" class="w-64 flex-shrink-0">
        <slot name="sidebar" />
      </aside>
    </div>
  </BasePageLayout>
</template>

<script setup>
/**
 * TabbedPageLayout
 * Layout component providing a header slot, tab navigation, and optional sidebar.
 *
 * Props:
 * - tabs: array of tab labels displayed in navigation
 * - modelValue: currently active tab (used with v-model)
 */
import { computed } from 'vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'

const props = defineProps({
  /** Array of tab labels */
  tabs: { type: Array, default: () => [] },
  /** Currently selected tab */
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const activeTab = computed({
  get: () => props.modelValue || props.tabs[0],
  set: (val) => emit('update:modelValue', val),
})

function selectTab(tab) {
  activeTab.value = tab
}
</script>
