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
      :account-options="forecastAccounts"
      :included-account-ids="includedAccountIds"
      :excluded-account-ids="excludedAccountIds"
      @update:manualIncome="manualIncome = $event"
      @update:liabilityRate="liabilityRate = $event"
      @update:includedAccountIds="includedAccountIds = $event"
      @update:excludedAccountIds="excludedAccountIds = $event"
    />

    <div class="card glass text-sm control-row">
      <label>
        Graph mode
        <select v-model="graphMode" class="input ml-2">
          <option value="combined">Combined</option>
          <option value="forecast">Forecast only</option>
          <option value="historical">Historical only</option>
        </select>
      </label>
      <label>
        Moving average
        <select v-model.number="movingAverageWindow" class="input ml-2">
          <option :value="7">7 days</option>
          <option :value="30">30 days</option>
          <option :value="60">60 days</option>
          <option :value="90">90 days</option>
        </select>
      </label>
      <label> <input v-model="normalize" type="checkbox" class="mr-1" /> Normalize history </label>
    </div>

    <ForecastChart
      :timeline="timeline"
      :view-type="viewType"
      :graph-mode="graphMode"
      :realized-history="realizedHistory"
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
  type ForecastGraphMode,
  type ForecastViewType,
  useForecastData,
} from '@/composables/useForecastData'
import api from '@/services/api'

type ForecastAccountOption = {
  account_id: string
  name: string
  institution_name?: string
}

const viewType = ref<ForecastViewType>('Month')
const currentBalance = ref(0)
const manualIncome = ref(0)
const liabilityRate = ref(0)
const adjustments = ref<ForecastAdjustmentInput[]>([])
const userId = ref(import.meta.env.VITE_USER_ID_PLAID || '')
const forecastAccounts = ref<ForecastAccountOption[]>([])
const includedAccountIds = ref<string[]>([])
const excludedAccountIds = ref<string[]>([])
const movingAverageWindow = ref<7 | 30 | 60 | 90>(30)
const normalize = ref(false)
const graphMode = ref<ForecastGraphMode>('combined')

const { timeline, summary, cashflows, loading, error, fetchData } = useForecastData({
  viewType,
  manualIncome,
  liabilityRate,
  adjustments,
  userId,
  includedAccountIds,
  excludedAccountIds,
  movingAverageWindow,
  normalize,
  graphMode,
})

const forecastItems = computed(() =>
  cashflows.value.map((item) => ({
    label: item.label,
    amount: item.amount,
  })),
)
const hasForecastData = computed(() => timeline.value.length > 0)
const isLoading = computed(() => loading.value)
const realizedHistory = computed(() => (summary.value?.metadata?.realized_history as any[]) ?? [])

watch(summary, (value) => {
  currentBalance.value = value?.starting_balance ?? 0
})

onMounted(async () => {
  await fetchForecastAccounts()
  await fetchData()
})

watch(
  [
    viewType,
    manualIncome,
    liabilityRate,
    adjustments,
    includedAccountIds,
    excludedAccountIds,
    movingAverageWindow,
    normalize,
    graphMode,
  ],
  fetchData,
)

/**
 * Load forecast account options and default to including all visible accounts.
 */
async function fetchForecastAccounts() {
  try {
    const response = await api.getAccounts()
    const accounts = Array.isArray(response.accounts) ? response.accounts : []
    forecastAccounts.value = accounts.map((account) => ({
      account_id: account.account_id,
      name: account.name,
      institution_name: account.institution_name,
    }))
    if (includedAccountIds.value.length === 0) {
      includedAccountIds.value = forecastAccounts.value.map((account) => account.account_id)
    }
  } catch {
    forecastAccounts.value = []
  }
}

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

.control-row {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}
</style>
