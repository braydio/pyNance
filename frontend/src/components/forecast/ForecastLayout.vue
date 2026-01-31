<template>
  <div class="forecast-layout p-6 bg-gray-50 space-y-6">
    <div v-if="error" class="card glass text-sm text-red-600">
      {{ error.message }}
    </div>
    <div v-else-if="isLoading" class="card glass text-sm text-gray-500">
      Loading forecast data...
    </div>
    <div v-else-if="!hasForecastData" class="card glass text-sm text-gray-500">
      Forecast data is not available yet. Add adjustments or try again later.
    </div>
    <ForecastSummaryPanel
      :current-balance="currentBalance"
      :manual-income="manualIncome"
      :liability-rate="liabilityRate"
      :view-type="viewType"
      @update:manualIncome="manualIncome = $event"
      @update:liabilityRate="liabilityRate = $event"
    />

    <ForecastChart
      :timeline="timeline"
      :view-type="viewType"
      @update:viewType="viewType = $event"
    />

    <ForecastBreakdown :forecast-items="forecastItems" :view-type="viewType" />

    <ForecastAdjustmentsForm @add-adjustment="addAdjustment" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import ForecastSummaryPanel from './ForecastSummaryPanel.vue'
import ForecastChart from './ForecastChart.vue'
import ForecastBreakdown from './ForecastBreakdown.vue'
import ForecastAdjustmentsForm from './ForecastAdjustmentsForm.vue'
import {
  type ForecastAdjustmentInput,
  type ForecastViewType,
  useForecastData,
} from '@/composables/useForecastData'

const viewType = ref<ForecastViewType>('Month')
const currentBalance = ref(0)
const manualIncome = ref(0)
const liabilityRate = ref(0)
const adjustments = ref<ForecastAdjustmentInput[]>([])
const userId = ref(import.meta.env.VITE_USER_ID_PLAID || '')

const { timeline, summary, cashflows, loading, error, fetchData } = useForecastData({
  viewType,
  manualIncome,
  liabilityRate,
  adjustments,
  userId,
})

const forecastItems = computed(() =>
  cashflows.value.map((item) => ({
    label: item.label,
    amount: item.amount,
  }))
)
const hasForecastData = computed(() => timeline.value.length > 0)
const isLoading = computed(() => loading.value)

watch(summary, (value) => {
  currentBalance.value = value?.starting_balance ?? 0
})

onMounted(fetchData)
watch([viewType, manualIncome, liabilityRate, adjustments], fetchData)

/**
 * Capture adjustment inputs so the compute request can include them.
 */
function addAdjustment(adjustment: ForecastAdjustmentInput) {
  adjustments.value = [...adjustments.value, adjustment]
}
</script>

<style scoped>
@reference "../../assets/css/main.css";
.forecast-layout {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
</style>
