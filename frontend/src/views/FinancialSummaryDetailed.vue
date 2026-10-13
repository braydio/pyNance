<!-- FinancialSummaryDetailed.vue
  Standalone view displaying DailyNetChart with expanded financial summary metrics.
-->
<template>
  <BasePageLayout class="financial-summary-detailed" gap="gap-8">
    <PageHeader :icon="BarChart3">
      <template #title>Financial Summary</template>
      <template #subtitle>Net income and spending for the selected period</template>
    </PageHeader>
    <div class="flex justify-end">
      <DateRangeSelector
        v-model:start-date="dateRange.start"
        v-model:end-date="dateRange.end"
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
import { BarChart3 } from 'lucide-vue-next'
import PageHeader from '@/components/ui/PageHeader.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import FinancialSummary from '@/components/statistics/FinancialSummary.vue'

const dateRange = ref({ start: '', end: '' })
const zoomedOut = ref(false)
const summary = ref({})
const chartData = ref([])
</script>
