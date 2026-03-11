<!--
  CategoryBreakdownSection.vue
  Displays spending breakdown controls and chart results.
-->
<template>
  <div
    class="md:col-span-2 w-full bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-yellow)] p-6 flex flex-col gap-4 overflow-hidden"
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
    <div v-if="storyCards.length" class="breakdown-story-grid">
      <article v-for="card in storyCards" :key="card.label" class="breakdown-story-card">
        <div class="breakdown-story-label">{{ card.label }}</div>
        <div class="breakdown-story-value">{{ card.value }}</div>
        <p class="breakdown-story-copy">{{ card.copy }}</p>
      </article>
    </div>
    <CategoryBreakdownChart
      :start-date="startDate"
      :end-date="endDate"
      :selected-category-ids="selectedCategoryIds"
      :group-others="groupOthers"
      :breakdown-type="breakdownType"
      @summary-change="emit('summary-change', $event)"
      @categories-change="emit('categories-change', $event)"
      @rows-change="visibleRows = $event"
      @bar-click="emit('bar-click', $event)"
    />

    <div v-if="visibleRows.length" class="breakdown-rows-shell">
      <div class="breakdown-rows-header">
        <span>Visible ranking</span>
        <span>{{ visibleRows.length }} rows</span>
      </div>
      <ol class="breakdown-rows-list">
        <li v-for="(row, index) in visibleRows.slice(0, 5)" :key="`${row.label}-${index}`" class="breakdown-row-item">
          <span class="breakdown-row-rank">{{ index + 1 }}</span>
          <div class="breakdown-row-main">
            <span class="breakdown-row-label">{{ row.label }}</span>
            <span v-if="row.parentLabel" class="breakdown-row-parent">{{ row.parentLabel }}</span>
          </div>
          <div class="breakdown-row-metrics">
            <span class="breakdown-row-amount">{{ formatAmount(row.amount) }}</span>
            <span class="breakdown-row-share">{{ shareOfTotal(row.amount) }}</span>
          </div>
        </li>
      </ol>
    </div>

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
import { computed, ref } from 'vue'
import ChartWidgetTopBar from '@/components/ui/ChartWidgetTopBar.vue'
import GroupedCategoryDropdown from '@/components/ui/GroupedCategoryDropdown.vue'
import CategoryBreakdownChart from '@/components/charts/CategoryBreakdownChart.vue'
import { formatAmount } from '@/utils/format'

const props = defineProps({
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

const visibleRows = ref([])

const totalVisibleAmount = computed(() =>
  visibleRows.value.reduce((sum, row) => sum + Number(row.amount || 0), 0),
)

const topRow = computed(() => visibleRows.value[0] || null)

const storyCards = computed(() => {
  if (!visibleRows.value.length) return []

  const concentration = topRow.value && totalVisibleAmount.value
    ? (Number(topRow.value.amount || 0) / totalVisibleAmount.value) * 100
    : 0

  return [
    {
      label: 'Top driver',
      value: topRow.value?.label || 'None',
      copy: topRow.value?.parentLabel
        ? `Largest visible item inside ${topRow.value.parentLabel}.`
        : 'Largest visible spend item in the current view.',
    },
    {
      label: 'Concentration',
      value: `${concentration.toFixed(1)}%`,
      copy: 'Share of the visible total held by the largest row.',
    },
    {
      label: 'Scope',
      value: `${props.selectedCategoryIds.length} selected`,
      copy:
        props.breakdownType === 'merchant'
          ? 'Merchant view is best for vendor-level drilling.'
          : 'Category view is best for budget-shape scanning.',
    },
  ]
})

function shareOfTotal(amount) {
  const total = totalVisibleAmount.value
  if (!total) return '0.0%'
  return `${((Number(amount || 0) / total) * 100).toFixed(1)}%`
}
</script>

<style scoped>
.breakdown-story-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.9rem;
}

.breakdown-story-card {
  border: 1px solid color-mix(in srgb, var(--color-accent-yellow) 26%, var(--divider));
  border-radius: 1rem;
  background: color-mix(in srgb, var(--color-bg-dark) 78%, transparent);
  padding: 0.95rem 1rem;
}

.breakdown-story-label {
  font-family: var(--font-display);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-accent-yellow);
}

.breakdown-story-value {
  margin-top: 0.35rem;
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text-light);
}

.breakdown-story-copy {
  margin: 0.35rem 0 0;
  font-size: 0.82rem;
  line-height: 1.55;
  color: color-mix(in srgb, var(--color-text-light) 72%, var(--color-text-muted));
}

.breakdown-rows-shell {
  border-top: 1px solid color-mix(in srgb, var(--divider) 82%, transparent);
  padding-top: 0.85rem;
}

.breakdown-rows-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.7rem;
  font-family: var(--font-display);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.breakdown-rows-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.breakdown-row-item {
  display: grid;
  grid-template-columns: 1.8rem minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.75rem;
  border-radius: 0.9rem;
  background: color-mix(in srgb, var(--color-bg-dark) 72%, transparent);
  border: 1px solid color-mix(in srgb, var(--divider) 74%, transparent);
  padding: 0.65rem 0.8rem;
}

.breakdown-row-rank {
  font-family: var(--font-display);
  color: var(--color-accent-yellow);
}

.breakdown-row-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.breakdown-row-label {
  font-weight: 700;
  color: var(--color-text-light);
}

.breakdown-row-parent {
  font-size: 0.76rem;
  color: var(--color-text-muted);
}

.breakdown-row-metrics {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.15rem;
}

.breakdown-row-amount {
  font-weight: 700;
  color: var(--color-accent-cyan);
}

.breakdown-row-share {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

@media (max-width: 900px) {
  .breakdown-story-grid {
    grid-template-columns: 1fr;
  }
}
</style>
