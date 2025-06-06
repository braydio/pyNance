<template>
  <div class="forecast-layout p-6 bg-gray-50 space-y-6">
    <ForecastSummaryPanel :current-balance="currentBalance" :manual-income="manualIncome"
      :liability-rate="liabilityRate" :view-type="viewType" @update:manualIncome="manualIncome = $event"
      @update:liabilityRate="liabilityRate = $event" />

    <ForecastChart :forecast-items="forecastItems" :account-history="accountHistory" :manual-income="manualIncome"
      :liability-rate="liabilityRate" :view-type="viewType" @update:viewType="viewType = $event" />

    <ForecastBreakdown :forecast-items="forecastItems" :view-type="viewType" />

    <ForecastAdjustmentsForm @add-adjustment="addAdjustment" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import ForecastSummaryPanel from './ForecastSummaryPanel.vue'
import ForecastChart from './ForecastChart.vue'
import ForecastBreakdown from './ForecastBreakdown.vue'
import ForecastAdjustmentsForm from './ForecastAdjustmentsForm.vue'
import { useForecastData } from '@/composables/useForecastData'
import { computed } from 'vue'

const viewType = ref<'Month' | 'Year'>('Month')
const currentBalance = ref(0)
const manualIncome = ref(0)
const liabilityRate = ref(0)

const { labels, forecast, actuals, loading, error, fetchData } = useForecastData(
  viewType,
  manualIncome,
  liabilityRate
)

const forecastItems = computed(() =>
  labels.value.map((label, i) => ({ label, amount: forecast.value[i] }))
)
const accountHistory = computed(() =>
  labels.value.map((label, i) => ({ date: label, balance: actuals.value[i] ?? 0 }))
)

onMounted(fetchData)
watch([viewType, manualIncome, liabilityRate], fetchData)

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
