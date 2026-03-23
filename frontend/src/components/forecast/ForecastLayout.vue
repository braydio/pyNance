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
      :asset-balance="assetBalance"
      :liability-balance="liabilityBalance"
      :net-balance="netBalance"
      :manual-income="manualIncome"
      :liability-rate="liabilityRate"
      :net-change="summary?.net_change ?? null"
      :view-type="viewType"
      :account-options="forecastAccounts"
      :account-group-options="accountGroupOptions"
      :included-account-ids="includedAccountIds"
      :excluded-account-ids="excludedAccountIds"
      :compute-meta="forecastComputeMeta"
      @update:manualIncome="manualIncome = $event"
      @update:liabilityRate="liabilityRate = $event"
      @update:includedAccountIds="includedAccountIds = $event"
      @update:excludedAccountIds="excludedAccountIds = $event"
    />

    <div class="card glass text-sm control-row">
      <label>
        Chart aspect
        <select v-model="selectedAspect" class="input ml-2">
          <option v-for="aspect in forecastAspectOptions" :key="aspect.value" :value="aspect.value">
            {{ aspect.label }}
          </option>
        </select>
      </label>
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
      <label><input v-model="normalize" type="checkbox" class="mr-1" /> Normalize history</label>
    </div>

    <div class="card glass adjustments-grid">
      <div>
        <h3 class="adjustments-title">Manual Adjustments</h3>
        <p v-if="manualAdjustmentPoints.length === 0" class="adjustments-empty">
          No manual adjustments applied.
        </p>
        <ul v-else class="adjustments-list">
          <li v-for="(item, idx) in manualAdjustmentPoints" :key="`manual-${idx}`">
            <span>{{ item.label || 'Manual adjustment' }} ({{ item.date || 'scheduled' }})</span>
            <strong>{{ item.value < 0 ? '-' : '+' }}${{ Math.abs(item.value).toFixed(2) }}</strong>
          </li>
        </ul>
      </div>
      <div>
        <h3 class="adjustments-title">Realized Income Used for Auto-Calculation</h3>
        <p v-if="realizedIncomePoints.length === 0" class="adjustments-empty">
          No realized income points were provided for auto-calculation.
        </p>
        <ul v-else class="adjustments-list auto">
          <li v-for="(item, idx) in realizedIncomePoints" :key="`auto-${idx}`">
            <span>{{ item.label || 'Realized income' }} ({{ item.date || 'scheduled' }})</span>
            <strong>{{ item.value < 0 ? '-' : '+' }}${{ Math.abs(item.value).toFixed(2) }}</strong>
          </li>
        </ul>
      </div>
    </div>

    <ForecastChart
      :timeline="timeline"
      :view-type="viewType"
      :graph-mode="graphMode"
      :realized-history="realizedHistory"
      :series="series"
      :selected-aspect="selectedAspect"
      :compute-meta="forecastComputeMeta"
      @update:viewType="viewType = $event"
    />

    <ForecastBreakdown :forecast-items="forecastItems" :view-type="viewType" />

    <ForecastAdjustmentsForm @add-adjustment="addAdjustment" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import ForecastAdjustmentsForm from './ForecastAdjustmentsForm.vue'
import ForecastBreakdown from './ForecastBreakdown.vue'
import ForecastChart from './ForecastChart.vue'
import ForecastSummaryPanel from './ForecastSummaryPanel.vue'
import { useForecastData } from '@/composables/useForecastData'
import { useAccountGroups } from '@/composables/useAccountGroups'
import api from '@/services/api'

const FORECAST_ASPECT_OPTIONS = [
  { value: 'balances', label: 'Balances' },
  { value: 'realized_income', label: 'Realized income' },
  { value: 'manual_adjustments', label: 'Manual adjustments' },
  { value: 'spending', label: 'Spending' },
  { value: 'debt_totals', label: 'Debt totals' },
]

const viewType = ref('Month')
const manualIncome = ref(0)
const liabilityRate = ref(0)
const adjustments = ref([])
const userId = ref(import.meta.env.VITE_USER_ID_PLAID || '')
const forecastAccounts = ref([])
const includedAccountIds = ref([])
const excludedAccountIds = ref([])
const movingAverageWindow = ref(30)
const normalize = ref(false)
const graphMode = ref('combined')
const selectedAspect = ref('balances')
const forecastAspectOptions = computed(() => FORECAST_ASPECT_OPTIONS)
const { groups: accountSnapshotGroups } = useAccountGroups({ userId: userId.value })

const {
  timeline,
  summary,
  adjustments: appliedAdjustments,
  series,
  metadata,
  loading,
  error,
  fetchData,
} = useForecastData({
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

const assetBalance = computed(() =>
  Number(metadata.value?.asset_balance ?? summary.value?.metadata?.asset_balance ?? 0),
)
const liabilityBalance = computed(() =>
  Number(metadata.value?.liability_balance ?? summary.value?.metadata?.liability_balance ?? 0),
)
const netBalance = computed(() =>
  Number(metadata.value?.net_balance ?? summary.value?.starting_balance ?? 0),
)

const seriesEntries = computed(() =>
  Object.values(series.value ?? {}).filter((entry) => Array.isArray(entry?.points)),
)
const forecastItems = computed(() =>
  seriesEntries.value.map((entry) => ({
    label: entry.label,
    amount: entry.points.reduce((total, point) => total + Number(point.value ?? 0), 0),
  })),
)
const baselineTrendAdjustment = computed(() => {
  const avgDaily = Number(summary.value?.average_daily_change ?? 0)
  if (!Number.isFinite(avgDaily) || avgDaily === 0) {
    return null
  }

  return {
    label: `Historical ${movingAverageWindow.value}d avg/day`,
    amount: avgDaily,
    date: 'daily trend',
    adjustment_type: 'auto_trend',
    reason: 'Derived from historical average net change.',
  }
})
const autoDetectedAdjustments = computed(() => [
  ...(appliedAdjustments.value || []).filter((adjustment) =>
    String(adjustment?.adjustment_type || '')
      .toLowerCase()
      .startsWith('auto'),
  ),
  ...(baselineTrendAdjustment.value ? [baselineTrendAdjustment.value] : []),
])
const manualAdjustmentSeries = computed(() => series.value?.manual_adjustments ?? null)
const realizedIncomeSeries = computed(() => series.value?.realized_income ?? null)
const manualAdjustmentPoints = computed(() =>
  (manualAdjustmentSeries.value?.points || []).filter((point) => Number(point.value ?? 0) !== 0),
)
const realizedIncomePoints = computed(() =>
  (realizedIncomeSeries.value?.points || []).filter((point) => Number(point.value ?? 0) !== 0),
)
const forecastAccountIdSet = computed(
  () => new Set(forecastAccounts.value.map((account) => account.account_id)),
)
const accountGroupOptions = computed(() =>
  (accountSnapshotGroups.value || [])
    .map((group) => {
      const uniqueAccountIds = Array.from(
        new Set(
          (group?.accounts || [])
            .map((account) => String(account?.account_id || account?.id || ''))
            .filter((id) => id && forecastAccountIdSet.value.has(id)),
        ),
      )

      return {
        id: String(group?.id || ''),
        name: String(group?.name || 'Group'),
        accountIds: uniqueAccountIds,
      }
    })
    .filter((group) => group.id && group.accountIds.length > 0),
)
const hasForecastData = computed(
  () => timeline.value.length > 0 || seriesEntries.value.some((entry) => entry.points.length > 0),
)
const isLoading = computed(() => loading.value)
const realizedHistory = computed(() => {
  const value = metadata.value?.realized_history ?? summary.value?.metadata?.realized_history
  return Array.isArray(value) ? value : []
})

const forecastComputeMeta = computed(() => ({
  lookbackDays: Number(
    metadata.value?.lookback_days ??
      summary.value?.metadata?.lookback_days ??
      metadata.value?.realized_history_lookback_days ??
      summary.value?.metadata?.realized_history_lookback_days ??
      realizedHistory.value.length ??
      0,
  ),
  movingAverageWindow: Number(
    metadata.value?.moving_average_window ??
      summary.value?.metadata?.moving_average_window ??
      movingAverageWindow.value,
  ),
  normalize: Boolean(
    metadata.value?.normalize ?? summary.value?.metadata?.normalize ?? normalize.value,
  ),
  includesAutoDetectedAdjustments: autoDetectedAdjustments.value.length > 0,
  autoDetectedAdjustmentCount: autoDetectedAdjustments.value.length,
}))

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
      account_id: String(account.account_id || ''),
      name: String(account.name || 'Account'),
      institution_name: String(account.institution_name || ''),
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
function addAdjustment(adjustment) {
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

.adjustments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
}

.adjustments-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 0.4rem;
}

.adjustments-empty {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.adjustments-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.35rem;
}

.adjustments-list li {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.adjustments-list.auto strong {
  color: #047857;
}
</style>
