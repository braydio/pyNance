<!--
  CategoryBreakdownSection.vue
  Displays spending breakdown controls and chart results.
-->
<template>
  <div
    class="md:col-span-2 w-full bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-yellow)] p-6 flex flex-col gap-3 overflow-hidden"
  >
    <div class="flex items-center justify-between mb-2">
      <div class="flex flex-col">
        <h2 class="text-xl font-bold text-[var(--color-accent-yellow)]">
          Spending by
          {{ breakdownType === 'merchant' ? 'Merchant' : 'Category' }}
        </h2>
        <slot name="subtitle" />
      </div>
      <ChartWidgetTopBar>
        <template #controls>
          <div class="flex flex-wrap gap-2 items-center">
            <div class="inline-flex rounded-lg border border-[var(--divider)] overflow-hidden">
              <button
                class="px-3 py-1 text-sm transition"
                :class="
                  breakdownType === 'category'
                    ? 'bg-[var(--color-accent-yellow)] text-[var(--color-bg)]'
                    : 'text-muted hover:bg-[var(--color-bg-dark)]'
                "
                @click="emit('change-breakdown', 'category')"
              >
                Categories
              </button>
              <button
                class="px-3 py-1 text-sm transition"
                :class="
                  breakdownType === 'merchant'
                    ? 'bg-[var(--color-accent-yellow)] text-[var(--color-bg)]'
                    : 'text-muted hover:bg-[var(--color-bg-dark)]'
                "
                @click="emit('change-breakdown', 'merchant')"
              >
                Merchants
              </button>
            </div>
            <GroupedCategoryDropdown
              v-if="breakdownType === 'category'"
              :groups="categoryGroups"
              :modelValue="selectedCategoryIds"
              @update:modelValue="emit('update-selection', $event)"
              class="w-full md:w-64"
            />
            <button class="btn btn-outline hover-lift" @click="emit('toggle-group-others')">
              {{ groupOthers ? 'Expand All' : 'Consolidate Minor Items' }}
            </button>
          </div>
        </template>
      </ChartWidgetTopBar>
    </div>
    <CategoryBreakdownChart
      :start-date="startDate"
      :end-date="endDate"
      :selected-category-ids="selectedCategoryIds"
      :group-others="groupOthers"
      :breakdown-type="breakdownType"
      @summary-change="emit('summary-change', $event)"
      @categories-change="emit('categories-change', $event)"
      @bar-click="emit('bar-click', $event)"
    />

    <div class="mt-1 flex items-center gap-2">
      <span class="font-bold">Total:</span>
      <span class="text-[var(--color-accent-cyan)] font-bold">{{
        formatAmount(summary.total)
      }}</span>
      <slot name="after-total" />
    </div>
  </div>
</template>

<script setup>
/**
 * Spending breakdown controls and chart wrapper.
 */
import ChartWidgetTopBar from '@/components/ui/ChartWidgetTopBar.vue'
import GroupedCategoryDropdown from '@/components/ui/GroupedCategoryDropdown.vue'
import CategoryBreakdownChart from '@/components/charts/CategoryBreakdownChart.vue'
import { formatAmount } from '@/utils/format'

defineProps({
  startDate: { type: String, default: '' },
  endDate: { type: String, default: '' },
  categoryGroups: { type: Array, default: () => [] },
  selectedCategoryIds: { type: Array, default: () => [] },
  groupOthers: { type: Boolean, default: true },
  breakdownType: { type: String, default: 'category' },
  summary: {
    type: Object,
    default: () => ({ total: 0, startDate: '', endDate: '' }),
  },
})

const emit = defineEmits([
  'change-breakdown',
  'toggle-group-others',
  'update-selection',
  'categories-change',
  'summary-change',
  'bar-click',
])
</script>
