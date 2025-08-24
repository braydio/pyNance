<!--
  FinancialSummaryDetailed.vue
  Standalone view rendering the FinancialSummary component with
  extended metrics enabled by default.
-->
<template>
  <div class="p-6">
    <FinancialSummary
      :summary="summary"
      :chart-data="chartData"
      :zoomed-out="false"
      default-extended
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import FinancialSummary from '@/components/statistics/FinancialSummary.vue'
import { fetchDailyNet } from '@/api/charts'

const summary = ref({
  totalIncome: 0,
  totalExpenses: 0,
  totalNet: 0,
  aboveAvgIncomeDays: 0,
  aboveAvgExpenseDays: 0,
})
const chartData = ref([])

onMounted(async () => {
  const response = await fetchDailyNet()
  if (response.status === 'success') {
    chartData.value = response.data
    computeSummary()
  }
})

function computeSummary() {
  const data = chartData.value
  const totalIncome = data.reduce((sum, d) => sum + (d.income?.parsedValue || 0), 0)
  const totalExpenses = data.reduce((sum, d) => sum + (d.expenses?.parsedValue || 0), 0)
  const totalNet = data.reduce((sum, d) => sum + (d.net?.parsedValue || 0), 0)
  const days = data.length || 1
  const avgIncome = totalIncome / days
  const avgExpenses = totalExpenses / days
  summary.value = {
    totalIncome,
    totalExpenses,
    totalNet,
    aboveAvgIncomeDays: data.filter((d) => (d.income?.parsedValue || 0) > avgIncome).length,
    aboveAvgExpenseDays: data.filter((d) => Math.abs(d.expenses?.parsedValue || 0) > Math.abs(avgExpenses)).length,
  }
}
</script>
