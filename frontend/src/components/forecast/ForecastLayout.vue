<template>
  <div class="forecast-layout p-6 bg-gray-50 space-y-6">
    <ForecastSummaryPanel :current-balance="currentBalance" :manual-income="manualIncome"
      :liability-rate="liabilityRate" :view-type="viewType" @update:manualIncome="manualIncome = $event"
      @update:liabilityRate="liabilityRate = $event" />

    <ForecastChart :forecast-items="forecastItems" :view-type="viewType" :manual-income="manualIncome"
      :liability-rate="liabilityRate" :account-history="accountHistory" @update:viewType="viewType = $event" />

    <ForecastBreakdown :forecast-items="forecastItems" :view-type="viewType" />

    <ForecastAdjustmentsForm @add-adjustment="addAdjustment" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ForecastSummaryPanel from './ForecastSummaryPanel.vue'
import ForecastChart from './ForecastChart.vue'
import ForecastBreakdown from './ForecastBreakdown.vue'
import ForecastAdjustmentsForm from './ForecastAdjustmentsForm.vue'

const viewType = ref < 'Month' | 'Year' > ('Month')
const currentBalance = ref(4200)
const manualIncome = ref(0)
const liabilityRate = ref(0)

const forecastItems = ref([
  { label: 'Salary', amount: 5000, frequency: 'monthly', nextDueDate: '2025-05-01' },
  { label: 'Rent', amount: -1500, frequency: 'monthly', nextDueDate: '2025-05-01' },
  { label: 'Utilities', amount: -200, frequency: 'monthly', nextDueDate: '2025-05-03' }
])

const accountHistory = ref([
  { date: '2025-05-01', balance: 4200 },
  { date: '2025-05-02', balance: 4400 },
  { date: '2025-05-03', balance: 4600 }
])

function addAdjustment(adjustment) {
  forecastItems.value.push(adjustment)
}
</script>

<style scoped>
.forecast-layout {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
</style>
