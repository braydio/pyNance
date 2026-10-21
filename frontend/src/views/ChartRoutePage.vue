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
      <div class="flex flex-wrap items-end justify-end gap-3">
        <ChartRangePresets v-model="selectedPreset" @update:model-value="applyPreset" />
        <DateRangeSelector
          :start-date="dateRange.start"
          :end-date="dateRange.end"
          disable-zoom
          @update:start-date="setManualDate('start', $event)"
          @update:end-date="setManualDate('end', $event)"
        />
      </div>
      <p class="text-sm text-muted" data-testid="chart-route-period">
        {{ dateRange.start }} – {{ dateRange.end }}
      </p>
    </template>

    <section class="chart-route-page__panel" :aria-label="heading.title">
      <div v-if="variant === 'cashflow'" role="group" aria-label="Chart measure" class="flex gap-2">
        <button
          v-for="option in NET_BASIS_OPTIONS"
          :key="option.value"
          type="button"
          class="btn btn-sm"
          :class="netBasis === option.value ? 'btn-primary' : 'btn-outline'"
          :aria-pressed="netBasis === option.value"
          :data-testid="`chart-route-basis-${option.value}`"
          @click="netBasis = option.value"
        >
          {{ option.label }}
        </button>
      </div>
      <DailyNetChart
        v-if="variant === 'cashflow'"
        :start-date="dateRange.start"
        :end-date="dateRange.end"
        :timeframe="selectedPreset"
        :basis="netBasis"
      >
        <template #title="{ granularityTitle }">
          <div class="flex flex-wrap items-center gap-3">
            <p class="text-sm text-muted" data-testid="chart-route-granularity">
              {{ netBasis === 'cash' ? 'Cash Movement' : 'Economic Net' }} · {{ granularityTitle }}
            </p>
          </div>
        </template>
      </DailyNetChart>

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
          :breakdown-type="breakdownType"
          @categories-change="setAvailableIds"
        />
      </template>

      <NetYearComparisonChart v-else />
    </section>
  </BasePageLayout>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { BarChart3, PieChart, TrendingUp } from 'lucide-vue-next'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'
import ChartRangePresets from '@/components/charts/ChartRangePresets.vue'
import GroupedCategoryDropdown from '@/components/ui/GroupedCategoryDropdown.vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import CategoryBreakdownChart from '@/components/charts/CategoryBreakdownChart.vue'
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue'
import { getMonthToDateRange, getChartPresetRange } from '@/composables/useDateRange'
import { useCategories } from '@/composables/useCategories'

const props = defineProps({
  /** Which chart this route shows. */
  variant: {
    type: String,
    required: true,
    validator: (value) => ['cashflow', 'category', 'year'].includes(value),
  },
})

const NET_BASIS_OPTIONS = [
  { value: 'cash', label: 'Cash Movement' },
  { value: 'economic', label: 'Economic Activity' },
]
/** Cash movement (money through checking and savings) is the default measure. */
const netBasis = ref('cash')

const HEADINGS = {
  cashflow: {
    title: 'Cash Flow',
    subtitle:
      'Cash movement or economic activity for the selected dates, bucketed to fit the period',
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

const heading = computed(() =>
  props.variant === 'category' && route.query.breakdown === 'merchant'
    ? { ...HEADINGS.category, title: 'Spending by Merchant' }
    : HEADINGS[props.variant],
)
const icon = computed(() => HEADINGS[props.variant].icon)

// Month-to-date, as local calendar dates (never UTC-shifted, never in the future).
const route = useRoute()
const isoDay = (value) => {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const d = new Date(`${value}T12:00:00`)
  return (
    !Number.isNaN(d.getTime()) &&
    d.getFullYear() === Number(value.slice(0, 4)) &&
    d.getMonth() + 1 === Number(value.slice(5, 7)) &&
    d.getDate() === Number(value.slice(8, 10))
  )
}
const fromQuery =
  isoDay(route.query.start_date) &&
  isoDay(route.query.end_date) &&
  route.query.start_date <= route.query.end_date
const dateRange = ref(
  fromQuery ? { start: route.query.start_date, end: route.query.end_date } : getMonthToDateRange(),
)
const selectedPreset = ref(fromQuery ? 'custom' : 'mtd')
function applyPreset(preset) {
  dateRange.value = getChartPresetRange(preset)
  selectedPreset.value = preset
}
function setManualDate(boundary, value) {
  dateRange.value[boundary] = value
  if (dateRange.value.start > dateRange.value.end) {
    dateRange.value[boundary === 'start' ? 'end' : 'start'] = value
  }
  selectedPreset.value = 'custom'
}

const {
  breakdownType,
  setBreakdownType,
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

onMounted(() => {
  if (route.query.breakdown === 'merchant') setBreakdownType('merchant')
  loadCategories()
})
watch(() => [dateRange.value.start, dateRange.value.end], loadCategories)
watch(
  () => route.query.breakdown,
  (mode) => {
    setBreakdownType(mode === 'merchant' ? 'merchant' : 'category')
    loadCategories()
  },
)
</script>
