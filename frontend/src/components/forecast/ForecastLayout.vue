<template>
  <div class="forecast-layout">
    <ForecastSummaryPanel :current-balance="currentBalance" :manual-income="manualIncome"
      :liability-rate="liabilityRate" :view-type="viewType" @update:manual-income="manualIncome = $event"
      @update:liability-rate="liabilityRate = $event" />
    <ForecastChart :forecast-items="forecastItems" :view-type="viewType" />
    <ForecastBreakdown :forecast-items="forecastItems" :view-type="viewType" />
    <ForecastAdjustmentsForm @add-adjustment="addAdjustment" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ForecastSummaryPanel from './ForecastSummaryPanel.vue'
import ForecastChart from './ForecastChart.vue'
import ForecastBreakdown from './ForecastBreakdown.vue'
import ForecastAdjustmentsForm from './ForecastAdjustmentsForm.vue'

const currentBalance = ref(10000)
const manualIncome = ref(5000)
const liabilityRate = ref(0.05)
const viewType = ref('Month')

const forecastItems = ref([
  { label: 'Salary', amount: 5000 },
  { label: 'Rent', amount: -1500 },
  { label: 'Utilities', amount: -200 },
])

function addAdjustment(adjustment) {
  forecastItems.value.push(adjustment)
}
</script>

<style scoped>
.forecast-layout {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
