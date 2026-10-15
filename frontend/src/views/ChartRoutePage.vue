<!--
  ChartRoutePage.vue
  Minimal page wrapper for the direct chart routes (/charts/cashflow, /charts/category,
  /charts/assets/year-comparison). Supplies the heading, a month-to-date range with working
  date inputs, and the loading/empty/error handling the bare chart components expect.
-->
<template>
  <BasePageLayout class="chart-route-page" gap="gap-6">
    <PageHeader :icon="icon">
      <template #title>{{ heading.title }}</template>
      <template #subtitle>{{ heading.subtitle }}</template>
    </PageHeader>

    <template v-if="variant !== 'year'">
      <div class="flex justify-end">
        <DateRangeSelector
          :start-date="dateRange.start"
          :end-date="dateRange.end"
          disable-zoom
          @update:start-date="dateRange.start = $event"
          @update:end-date="dateRange.end = $event"
        />
      </div>
      <p class="text-sm text-muted" data-testid="chart-route-period">
        {{ dateRange.start }} – {{ dateRange.end }}
      </p>
    </template>

    <section class="chart-route-page__panel" :aria-label="heading.title">
      <DailyNetChart
        v-if="variant === 'cashflow'"
        :start-date="dateRange.start"
        :end-date="dateRange.end"
      />

      <template v-else-if="variant === 'category'">
        <GroupedCategoryDropdown
          :groups="categoryGroups"
          :model-value="selectedIds"
          class="max-w-sm"
          @update:model-value="updateSelection"
        />
        <p v-if="!categoryGroups.length" class="text-sm text-muted" data-testid="chart-route-empty">
          No categories are available yet.
        </p>
        <CategoryBreakdownChart
          :start-date="dateRange.start"
          :end-date="dateRange.end"
          :selected-category-ids="selectedIds"
          :group-others="groupOthers"
          breakdown-type="category"
          @categories-change="setAvailableIds"
        />
      </template>

      <NetYearComparisonChart v-else />
    </section>
  </BasePageLayout>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { BarChart3, PieChart, TrendingUp } from 'lucide-vue-next'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'
import GroupedCategoryDropdown from '@/components/ui/GroupedCategoryDropdown.vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import CategoryBreakdownChart from '@/components/charts/CategoryBreakdownChart.vue'
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue'
import { getMonthToDateRange } from '@/composables/useDateRange'
import { useCategories } from '@/composables/useCategories'

const props = defineProps({
  /** Which chart this route shows. */
  variant: {
    type: String,
    required: true,
    validator: (value) => ['cashflow', 'category', 'year'].includes(value),
  },
})

const HEADINGS = {
  cashflow: {
    title: 'Cash Flow',
    subtitle: 'Daily net income for the selected dates',
    icon: BarChart3,
  },
  category: {
    title: 'Spending by Category',
    subtitle: 'Where money went in the selected dates',
    icon: PieChart,
  },
  year: {
    title: 'Year Comparison',
    subtitle: 'Assets, liabilities and net worth versus last year',
    icon: TrendingUp,
  },
}

const heading = computed(() => HEADINGS[props.variant])
const icon = computed(() => HEADINGS[props.variant].icon)

// Month-to-date, as local calendar dates (never UTC-shifted, never in the future).
const dateRange = ref(getMonthToDateRange())

const {
  groupedOptions: categoryGroups,
  selectedIds,
  groupOthers,
  setAvailableIds,
  updateSelection,
  refreshOptions,
} = useCategories()

function loadCategories() {
  if (props.variant !== 'category') return
  refreshOptions({ start_date: dateRange.value.start, end_date: dateRange.value.end })
}

onMounted(loadCategories)
watch(() => [dateRange.value.start, dateRange.value.end], loadCategories)
</script>
