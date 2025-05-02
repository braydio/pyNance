<script setup>
import { ref } from 'vue'
import ForecastSummaryPanel from './ForecastSummaryPanel.vue'
import ForecastAdjustmentsForm from './ForecastAdjustmentsForm.vue'
import ForecastChart from './ForecastChart.vue'
import ForecastBreakdown from './ForecastBreakdown.vue'

const currentBalance = ref(4200)
const forecastItems = ref([
  { label: 'Net Salary', amount: 3100 },
  { label: 'Subscription', amount: -25 },
  { label: 'Car Loan', amount: -220 },
])

const manualIncome = ref(0)
const liabilityRate = ref(0)
const viewType = ref('Month')

function updateView(newView) {
  viewType.value = newView
}
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <ForecastSummaryPanel :current-balance="currentBalance" :manual-income="manualIncome"
      :liability-rate="liabilityRate" :view-type="viewType" />

    <ForecastChart :forecast-items="forecastItems" :view-type="viewType" @update:viewType="updateView" />

    <ForecastBreakdown :forecast-items="forecastItems" :view-type="viewType" />

    <ForecastAdjustmentsForm @add-adjustment="item => forecastItems.push(item)" />
  </div>
</template>

<style scoped>
/* Forecast layout spacing and grid behavior */
</style>
