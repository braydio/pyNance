<template>
  <div class="p-6 space-y-6 max-w-5xl mx-auto">
    <h1 class="text-3xl font-bold text-center">30-Day Financial Forecast</h1>

    <ForecastSummaryPanel :current-balance="currentBalance" :manual-income="manualIncome"
      :liability-rate="liabilityRate" @update:manualIncome="manualIncome = $event"
      @update:liabilityRate="liabilityRate = $event" />

    <ForecastChart :forecast-items="forecastItems" />

    <ForecastBreakdown :forecast-items="forecastItemsWithAdjustments" />

    <ForecastAdjustmentsForm @addAdjustment="addAdjustment" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ForecastSummaryPanel from './ForecastSummaryPanel.vue'
import ForecastChart from './ForecastChart.vue'
import ForecastBreakdown from './ForecastBreakdown.vue'
import ForecastAdjustmentsForm from './ForecastAdjustmentsForm.vue'

const currentBalance = ref(4300)
const manualIncome = ref(200)
const liabilityRate = ref(2.1)

const baseItems = ref([
  { label: 'Salary', amount: 2500 },
  { label: 'Rent', amount: -1200 },
  { label: 'Subscriptions', amount: -200 },
  { label: 'Investment Returns', amount: 300 },
])

const adjustments = ref([])

const forecastItems = computed(() => baseItems.value)
const forecastItemsWithAdjustments = computed(() => [
  ...forecastItems.value,
  { label: 'Manual Income', amount: manualIncome.value },
  { label: 'Liability Impact', amount: -(currentBalance.value * liabilityRate.value / 100) },
  ...adjustments.value
])

function addAdjustment(item) {
  adjustments.value.push(item)
}
</script>
