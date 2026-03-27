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
      :net-change="summary?.net_change"
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
      <label> <input v-model="normalize" type="checkbox" class="mr-1" /> Normalize history </label>
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
            <strong>{{ formatSignedCurrency(item.value) }}</strong>
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
            <strong>{{ formatSignedCurrency(item.value) }}</strong>
          </li>
        </ul>
      </div>
    </div>

    <div class="card glass auto-adjustments-card">
      <div class="auto-adjustments-card__header">
        <div>
          <h3 class="adjustments-title">Auto-Detected Adjustments</h3>
          <p class="adjustments-empty">
            Review the transactions used to infer forecasted wage income when source references are
            available.
          </p>
        </div>
      </div>

      <p v-if="autoDetectedAdjustments.length === 0" class="adjustments-empty">
        No auto-detected adjustments are active for this forecast.
      </p>

      <ul v-else class="auto-adjustments-list">
        <li
          v-for="(adjustment, index) in autoDetectedAdjustments"
          :key="adjustmentKey(adjustment, index)"
          class="auto-adjustment-item"
        >
          <div class="auto-adjustment-item__summary">
            <div>
              <p class="auto-adjustment-item__label">
                {{ adjustment.label || 'Auto adjustment' }}
              </p>
              <p class="auto-adjustment-item__meta">
                {{ adjustment.date || 'scheduled' }}
                <span v-if="adjustment.reason">· {{ adjustment.reason }}</span>
              </p>
            </div>
            <div class="auto-adjustment-item__actions">
              <strong>{{ formatSignedCurrency(Number(adjustment.amount ?? 0)) }}</strong>
              <button
                v-if="sourceTransactionsForAdjustment(adjustment).length > 0"
                type="button"
                class="auto-adjustment-toggle"
                @click="toggleAdjustmentDetails(adjustment, index)"
              >
                {{
                  isAdjustmentExpanded(adjustment, index)
                    ? 'Hide source transactions'
                    : 'View source transactions'
                }}
              </button>
            </div>
          </div>

          <p
            v-if="sourceTransactionsForAdjustment(adjustment).length === 0"
            class="auto-adjustment-item__empty"
          >
            No source transactions are available for this auto-detected adjustment.
          </p>

          <div
            v-else-if="isAdjustmentExpanded(adjustment, index)"
            class="auto-adjustment-item__details"
          >
            <ul class="source-transactions-list">
              <li
                v-for="transaction in sourceTransactionsForAdjustment(adjustment)"
                :key="transaction.id || `${transaction.date}-${transaction.amount}`"
                class="source-transaction-item"
              >
                <div class="source-transaction-item__summary">
                  <div>
                    <p class="source-transaction-item__description">
                      {{ transaction.description || 'Transaction reference' }}
                    </p>
                    <p class="source-transaction-item__meta">
                      {{ transaction.date || 'Unknown date' }}
                      <span v-if="transaction.id">· {{ transaction.id }}</span>
                    </p>
                  </div>
                  <strong>{{ formatSignedCurrency(Number(transaction.amount ?? 0)) }}</strong>
                </div>
                <p
                  v-if="summarizeMatchingFields(transaction.matching_fields)"
                  class="source-transaction-item__matching"
                >
                  Matching fields: {{ summarizeMatchingFields(transaction.matching_fields) }}
                </p>
              </li>
            </ul>
          </div>
        </li>
      </ul>
    </div>

    <ForecastChart
      :timeline="timeline"
      :view-type="viewType"
      :graph-mode="graphMode"
      :realized-history="realizedHistory"
      :series="series"
      :selected-aspect="selectedAspect"
      :cashflows="cashflows"
      :asset-balance="assetBalance"
      :liability-balance="liabilityBalance"
      :net-balance="netBalance"
      :compute-meta="forecastComputeMeta"
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
  type ForecastAspectSeries,
  type ForecastGraphMode,
  type ForecastMetadata,
  type ForecastSeriesPoint,
  type ForecastViewType,
  useForecastData,
} from '@/composables/useForecastData'
import { useAccountGroups } from '@/composables/useAccountGroups'
import api from '@/services/api'

type ForecastComputeMeta = {
  lookbackDays: number
  movingAverageWindow: 7 | 30 | 60 | 90
  normalize: boolean
  includesAutoDetectedAdjustments: boolean
  autoDetectedAdjustmentCount: number
}

type ForecastAccountOption = {
  account_id: string
  name?: string
  institution_name?: string
}

type ForecastGroupOption = {
  id: string
  name: string
  accountIds: string[]
}

type SourceTransactionMatchingFields = {
  category?: string
  category_display?: string
  category_slug?: string
  personal_finance_category?: Record<string, unknown> | null
  plaid_category?: string[] | Record<string, unknown> | string | null
  tags?: string[]
}

type SourceTransactionReference = {
  id?: string
  date?: string
  amount?: number
  description?: string
  matching_fields?: SourceTransactionMatchingFields
}

type AdjustmentMetadata = ForecastMetadata & {
  source_transactions?: SourceTransactionReference[]
}

type ForecastAdjustmentWithMetadata = ForecastAdjustmentInput & {
  metadata?: AdjustmentMetadata
}

const FORECAST_ASPECT_OPTIONS = [
  { value: 'balances', label: 'Balances' },
  { value: 'realized_income', label: 'Realized income' },
  { value: 'manual_adjustments', label: 'Manual adjustments' },
  { value: 'spending', label: 'Spending' },
  { value: 'debt', label: 'Debt composition' },
] as const

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

const viewType = ref<ForecastViewType>('Month')
const manualIncome = ref(0)
const liabilityRate = ref(0)
const adjustments = ref<ForecastAdjustmentInput[]>([])
const userId = ref(String(import.meta.env.VITE_USER_ID_PLAID || ''))
const forecastAccounts = ref<ForecastAccountOption[]>([])
const includedAccountIds = ref<string[]>([])
const excludedAccountIds = ref<string[]>([])
const movingAverageWindow = ref<7 | 30 | 60 | 90>(30)
const normalize = ref(false)
const graphMode = ref<ForecastGraphMode>('combined')
const selectedAspect = ref('balances')
const expandedAdjustmentKeys = ref<string[]>([])

const forecastAspectOptions = computed(() => FORECAST_ASPECT_OPTIONS)
const { groups: accountSnapshotGroups } = useAccountGroups({ userId: userId.value })

const {
  timeline,
  summary,
  adjustments: appliedAdjustments,
  cashflows,
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

const seriesEntries = computed(() => Object.values(series.value || {}))
const forecastItems = computed(() =>
  seriesEntries.value.map((entry) => ({
    label: entry.label,
    amount: entry.points.reduce((total, point) => total + Number(point.value ?? 0), 0),
  })),
)
const baselineTrendAdjustment = computed<ForecastAdjustmentWithMetadata | null>(() => {
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
    metadata: {},
  }
})
const autoDetectedAdjustments = computed<ForecastAdjustmentWithMetadata[]>(() => [
  ...((appliedAdjustments.value || []).filter((adjustment) =>
    String(adjustment?.adjustment_type || '')
      .toLowerCase()
      .startsWith('auto'),
  ) as ForecastAdjustmentWithMetadata[]),
  ...(baselineTrendAdjustment.value ? [baselineTrendAdjustment.value] : []),
])
const manualAdjustmentSeries = computed<ForecastAspectSeries | null>(
  () => series.value?.manual_adjustments ?? null,
)
const realizedIncomeSeries = computed<ForecastAspectSeries | null>(
  () => series.value?.realized_income ?? null,
)
const manualAdjustmentPoints = computed<ForecastSeriesPoint[]>(() =>
  (manualAdjustmentSeries.value?.points || []).filter((point) => Number(point.value ?? 0) !== 0),
)
const realizedIncomePoints = computed<ForecastSeriesPoint[]>(() =>
  (realizedIncomeSeries.value?.points || []).filter((point) => Number(point.value ?? 0) !== 0),
)
const forecastAccountIdSet = computed(
  () => new Set(forecastAccounts.value.map((account) => account.account_id)),
)
const accountGroupOptions = computed<ForecastGroupOption[]>(() =>
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
  () => timeline.value.length > 0 || hasRenderableCashflows(cashflows.value),
)
const isLoading = computed(() => loading.value)
const realizedHistory = computed(
  () => metadata.value?.realized_history ?? summary.value?.metadata?.realized_history ?? [],
)

const forecastComputeMeta = computed<ForecastComputeMeta>(() => ({
  lookbackDays: Number(
    metadata.value?.lookback_days ??
      summary.value?.metadata?.lookback_days ??
      metadata.value?.realized_history_lookback_days ??
      summary.value?.metadata?.realized_history_lookback_days ??
      realizedHistory.value.length ??
      0,
  ),
  movingAverageWindow: movingAverageWindow.value,
  normalize: normalize.value,
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

watch(autoDetectedAdjustments, (nextAdjustments) => {
  const validKeys = new Set(
    nextAdjustments.map((adjustment, index) => adjustmentKey(adjustment, index)),
  )
  expandedAdjustmentKeys.value = expandedAdjustmentKeys.value.filter((key) => validKeys.has(key))
})

/**
 * Determine whether any cashflow items exist that can feed non-balance chart aspects.
 *
 * @param entries Cashflow entries returned by the forecast endpoint.
 * @returns Whether at least one non-zero cashflow exists.
 */
function hasRenderableCashflows(entries: Array<{ amount?: number | null }>) {
  return entries.some((entry) => Number(entry?.amount ?? 0) !== 0)
}

/**
 * Load forecast account options and default to including all visible accounts.
 *
 * @returns Promise resolving after account options are normalized.
 */
async function fetchForecastAccounts() {
  try {
    const response = await api.getAccounts()
    const accounts = Array.isArray(response.accounts) ? response.accounts : []
    forecastAccounts.value = accounts.map((account) => ({
      account_id: String(account.account_id || ''),
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
 *
 * @param adjustment New manual adjustment emitted by the form.
 */
function addAdjustment(adjustment: ForecastAdjustmentInput) {
  adjustments.value = [...adjustments.value, adjustment]
}

/**
 * Build a stable key for auto-detected adjustment expansion state.
 *
 * @param adjustment Adjustment rendered in the auto-detected list.
 * @param index Fallback list index for duplicate entries.
 * @returns Stable string key.
 */
function adjustmentKey(adjustment: ForecastAdjustmentInput, index: number) {
  return [
    adjustment.adjustment_type || 'adjustment',
    adjustment.date || 'scheduled',
    adjustment.label || 'Adjustment',
    String(adjustment.amount ?? 0),
    String(index),
  ].join('::')
}

/**
 * Toggle the drill-down panel for an auto-detected adjustment.
 *
 * @param adjustment Adjustment whose source transactions should be shown or hidden.
 * @param index Adjustment index used in the rendered list.
 */
function toggleAdjustmentDetails(adjustment: ForecastAdjustmentInput, index: number) {
  const key = adjustmentKey(adjustment, index)
  if (expandedAdjustmentKeys.value.includes(key)) {
    expandedAdjustmentKeys.value = expandedAdjustmentKeys.value.filter((item) => item !== key)
    return
  }
  expandedAdjustmentKeys.value = [...expandedAdjustmentKeys.value, key]
}

/**
 * Determine whether an adjustment's source transaction panel is expanded.
 *
 * @param adjustment Adjustment rendered in the auto-detected list.
 * @param index Adjustment index used in the rendered list.
 * @returns Whether the source transaction panel is open.
 */
function isAdjustmentExpanded(adjustment: ForecastAdjustmentInput, index: number) {
  return expandedAdjustmentKeys.value.includes(adjustmentKey(adjustment, index))
}

/**
 * Read source transaction references from adjustment metadata.
 *
 * @param adjustment Auto-detected adjustment returned by the API.
 * @returns Normalized source transaction references.
 */
function sourceTransactionsForAdjustment(
  adjustment: ForecastAdjustmentWithMetadata,
): SourceTransactionReference[] {
  const sourceTransactions = adjustment?.metadata?.source_transactions
  return Array.isArray(sourceTransactions) ? sourceTransactions : []
}

/**
 * Format signed currency values for forecast adjustment summaries.
 *
 * @param value Signed numeric amount.
 * @returns Signed USD string.
 */
function formatSignedCurrency(value: number) {
  const absoluteAmount = currencyFormatter.format(Math.abs(Number(value || 0)))
  return `${value < 0 ? '-' : '+'}${absoluteAmount}`
}

/**
 * Convert transaction matching fields into compact explanatory text.
 *
 * @param fields Category and tag fields captured during backend matching.
 * @returns Readable summary string for the drill-down UI.
 */
function summarizeMatchingFields(fields?: SourceTransactionMatchingFields) {
  if (!fields) {
    return ''
  }

  const parts: string[] = []
  if (fields.category_display) {
    parts.push(`display ${fields.category_display}`)
  }
  if (fields.category) {
    parts.push(`category ${fields.category}`)
  }
  if (fields.category_slug) {
    parts.push(`slug ${fields.category_slug}`)
  }

  const pfcPrimary = String(fields.personal_finance_category?.primary || '').trim()
  const pfcDetailed = String(fields.personal_finance_category?.detailed || '').trim()
  if (pfcPrimary || pfcDetailed) {
    parts.push(`PFC ${[pfcPrimary, pfcDetailed].filter(Boolean).join(' / ')}`)
  }

  const plaidCategory = fields.plaid_category
  if (Array.isArray(plaidCategory) && plaidCategory.length > 0) {
    parts.push(`Plaid ${plaidCategory.join(' / ')}`)
  } else if (plaidCategory && typeof plaidCategory === 'object') {
    parts.push(`Plaid ${Object.values(plaidCategory).filter(Boolean).join(' / ')}`)
  } else if (typeof plaidCategory === 'string' && plaidCategory.trim()) {
    parts.push(`Plaid ${plaidCategory}`)
  }

  if (Array.isArray(fields.tags) && fields.tags.length > 0) {
    parts.push(`tags ${fields.tags.join(', ')}`)
  }

  return parts.join(' · ')
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

.auto-adjustments-card {
  display: grid;
  gap: 1rem;
}

.auto-adjustments-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.75rem;
}

.auto-adjustment-item {
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 0.75rem;
  padding: 0.85rem 1rem;
  background: rgba(255, 255, 255, 0.55);
}

.auto-adjustment-item__summary,
.source-transaction-item__summary {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.auto-adjustment-item__label,
.source-transaction-item__description {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
}

.auto-adjustment-item__meta,
.source-transaction-item__meta,
.source-transaction-item__matching,
.auto-adjustment-item__empty {
  margin: 0.2rem 0 0;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.auto-adjustment-item__actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.45rem;
}

.auto-adjustment-toggle {
  border: 1px solid rgba(37, 99, 235, 0.25);
  border-radius: 999px;
  padding: 0.35rem 0.75rem;
  background: rgba(37, 99, 235, 0.08);
  color: #1d4ed8;
  font-size: 0.78rem;
  font-weight: 600;
}

.auto-adjustment-toggle:hover {
  background: rgba(37, 99, 235, 0.14);
}

.auto-adjustment-item__details {
  margin-top: 0.9rem;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
  padding-top: 0.9rem;
}

.source-transactions-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.75rem;
}

.source-transaction-item {
  border-radius: 0.65rem;
  background: rgba(248, 250, 252, 0.85);
  padding: 0.75rem 0.85rem;
}
</style>
