<!-- FinancialSummaryDetailed.vue
  Standalone view displaying DailyNetChart with expanded financial summary metrics.
-->
<template>
  <BasePageLayout class="financial-summary-detailed" gap="gap-8">
    <PageHeader :icon="BarChart3">
      <template #title>Financial Summary</template>
      <template #subtitle>Net income and spending for the selected period</template>
    </PageHeader>
    <div class="flex flex-wrap items-end justify-end gap-3">
      <ChartRangePresets v-model="selectedPreset" @update:model-value="applyPreset" />
      <DateRangeSelector
        :start-date="dateRange.start"
        :end-date="dateRange.end"
        @update:start-date="setManualDate('start', $event)"
        @update:end-date="setManualDate('end', $event)"
        v-model:zoomed-out="zoomedOut"
      />
    </div>
    <DailyNetChart
      :start-date="dateRange.start"
      :end-date="dateRange.end"
      :zoomed-out="zoomedOut"
      @summary-change="summary = $event"
      @data-change="chartData = $event"
    />
    <FinancialSummary
      :summary="summary"
      :chart-data="chartData"
      :zoomed-out="zoomedOut"
      :start-date="dateRange.start"
      :end-date="dateRange.end"
    />
  </BasePageLayout>
</template>

<script setup>
import { ref } from 'vue'
import { getMonthToDateRange, getChartPresetRange } from '@/composables/useDateRange'
import { BarChart3 } from 'lucide-vue-next'
import PageHeader from '@/components/ui/PageHeader.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'
import ChartRangePresets from '@/components/charts/ChartRangePresets.vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import FinancialSummary from '@/components/statistics/FinancialSummary.vue'

// Month-to-date, as local calendar dates, so the chart and summary have real bounds on load.
const dateRange = ref(getMonthToDateRange())
const selectedPreset = ref('mtd')
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
const zoomedOut = ref(false)
const summary = ref({})
const chartData = ref([])
</script>
