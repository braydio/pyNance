<template>
  <div class="forecast-layout">
    <div v-if="error" class="card glass text-sm text-negative" role="alert">
      {{ error.message }}
    </div>
    <div v-else-if="isLoading" class="card glass text-sm text-muted" role="status">
      Loading forecast data...
    </div>
    <div v-else-if="!hasForecastData" class="card glass text-sm text-muted" role="status">
      Forecast data is not available yet. Select at least one account in the scope above, or add an
      adjustment below, then try again.
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
      :model-version="appliedModelVersion"
      :liquidity="liquidity"
      :uncertainty="uncertainty"
      :net-worth="netWorth"
      :debt-payment-coverage="debtPaymentCoverage"
      @update:manualIncome="manualIncome = $event"
      @update:liabilityRate="liabilityRate = $event"
      @update:includedAccountIds="includedAccountIds = $event"
      @update:excludedAccountIds="excludedAccountIds = $event"
    />

    <div class="card glass text-sm control-row basic-controls" data-testid="basic-controls">
      <label class="control-field">
        <span class="control-field__label">Chart aspect</span>
        <select v-model="selectedAspect" class="input select control-field__input">
          <option v-for="aspect in forecastAspectOptions" :key="aspect.value" :value="aspect.value">
            {{ aspect.label }}
          </option>
        </select>
      </label>
    </div>

    <ForecastChart
      :timeline="timeline"
      :view-type="viewType"
      :graph-mode="graphMode"
      :realized-history="realizedHistory"
      :series="series"
      :selected-aspect="selectedAspect"
      :compute-meta="forecastComputeMeta"
      :model-version="appliedModelVersion"
      :scenario-lines="scenarioLines"
      @update:viewType="viewType = $event"
    />

    <ForecastScenarioComparison
      v-if="appliedModelVersion === 'v2'"
      v-model:selected-ids="selectedScenarioIds"
      :presets="SCENARIO_PRESETS"
      :results="scenarioResults"
      :loading="isLoading"
    />

    <ForecastBreakdown
      :forecast-items="forecastItems"
      :view-type="viewType"
      :model-version="appliedModelVersion"
      :drivers="drivers"
      :data-quality="dataQuality"
      @select-item="openCashflowModal"
    />

    <details class="card glass text-sm assumptions-details" data-testid="assumptions">
      <summary class="disclosure-summary">
        Forecast assumptions: {{ manualAdjustmentPoints.length }} manual,
        {{ autoDetectedAdjustments.length }} auto-detected. Review assumptions
      </summary>
      <div class="assumptions-details__body space-y-6">
        <div class="adjustments-grid">
          <div>
            <h3 class="adjustments-title">Manual Adjustments</h3>
            <p v-if="manualAdjustmentPoints.length === 0" class="adjustments-empty">
              No manual adjustments applied.
            </p>
            <ul v-else class="adjustments-list">
              <li v-for="(item, idx) in manualAdjustmentPoints" :key="`manual-${idx}`">
                <span
                  >{{ item.label || 'Manual adjustment' }} ({{ item.date || 'scheduled' }})</span
                >
                <strong>{{ formatSignedCurrency(item.value) }}</strong>
              </li>
            </ul>
          </div>
          <div>
            <h3 class="adjustments-title">
              {{
                appliedModelVersion === 'v2'
                  ? 'Projected Income Events'
                  : 'Realized Income Used for Auto-Calculation'
              }}
            </h3>
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

        <p
          v-if="appliedModelVersion === 'v2'"
          class="adjustments-empty"
          data-testid="v2-assumptions-note"
        >
          Detected bills and paychecks are listed under “What drives this forecast”. Everyday
          spending is estimated from your recent history and shown as typical spending.
        </p>
        <div v-else class="auto-adjustments-card">
          <div class="auto-adjustments-card__header">
            <div>
              <h3 class="adjustments-title">Auto-Detected Adjustments</h3>
              <p class="adjustments-empty">
                Review source transactions used to infer forecasted wage income and rent expense.
              </p>
            </div>
          </div>

          <p v-if="autoDetectedAdjustments.length === 0" class="adjustments-empty">
            No auto-detected adjustments are active for this forecast.
          </p>

          <div v-else class="auto-adjustments-groups">
            <div>
              <h4 class="auto-adjustments-group-title">Wage Income Detections</h4>
              <p v-if="autoDetectedWageAdjustments.length === 0" class="adjustments-empty">
                No wage income detections are active.
              </p>
              <ul v-else class="auto-adjustments-list">
                <li
                  v-for="(adjustment, index) in autoDetectedWageAdjustments"
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
                        <span v-if="adjustment.metadata?.confidence !== undefined">
                          · Confidence {{ Number(adjustment.metadata?.confidence).toFixed(2) }}
                        </span>
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
                          <strong>{{
                            formatSignedCurrency(Number(transaction.amount ?? 0))
                          }}</strong>
                        </div>
                        <p
                          v-if="summarizeMatchingFields(transaction.matching_fields)"
                          class="source-transaction-item__matching"
                        >
                          Matching fields:
                          {{ summarizeMatchingFields(transaction.matching_fields) }}
                        </p>
                      </li>
                    </ul>
                  </div>
                </li>
              </ul>
            </div>

            <div>
              <h4 class="auto-adjustments-group-title">Rent Expense Detections</h4>
              <p v-if="autoDetectedRentAdjustments.length === 0" class="adjustments-empty">
                No rent expense detections are active.
              </p>
              <ul v-else class="auto-adjustments-list auto-adjustments-list--rent">
                <li
                  v-for="(adjustment, index) in autoDetectedRentAdjustments"
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
                        <span v-if="adjustment.metadata?.confidence !== undefined">
                          · Confidence {{ Number(adjustment.metadata?.confidence).toFixed(2) }}
                        </span>
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
                          <strong>{{
                            formatSignedCurrency(Number(transaction.amount ?? 0))
                          }}</strong>
                        </div>
                        <p
                          v-if="summarizeMatchingFields(transaction.matching_fields)"
                          class="source-transaction-item__matching"
                        >
                          Matching fields:
                          {{ summarizeMatchingFields(transaction.matching_fields) }}
                        </p>
                      </li>
                    </ul>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </details>

    <details class="card glass text-sm advanced-controls" data-testid="advanced-controls">
      <summary class="disclosure-summary">Advanced model controls</summary>
      <div class="control-row advanced-controls__body">
        <label class="control-field">
          <span class="control-field__label">Forecast model</span>
          <select
            v-model="modelVersion"
            class="input select control-field__input"
            data-testid="model-version-select"
          >
            <option value="v2">Liquid cash (V2, recommended)</option>
            <option value="v1">Legacy average-delta (V1)</option>
          </select>
        </label>
        <template v-if="appliedModelVersion === 'v2'">
          <label class="control-check" data-testid="simulation-toggle">
            <input v-model="simulationEnabled" type="checkbox" /> Show likely range and shortfall
            chance
          </label>
        </template>
        <template v-else>
          <label class="control-field">
            <span class="control-field__label">Graph mode</span>
            <select v-model="graphMode" class="input select control-field__input">
              <option value="combined">Combined</option>
              <option value="forecast">Forecast only</option>
              <option value="historical">Historical only</option>
            </select>
          </label>
          <label class="control-field">
            <span class="control-field__label">Moving average</span>
            <select v-model.number="movingAverageWindow" class="input select control-field__input">
              <option :value="7">7 days</option>
              <option :value="30">30 days</option>
              <option :value="60">60 days</option>
              <option :value="90">90 days</option>
            </select>
          </label>
          <label class="control-check"
            ><input v-model="normalize" type="checkbox" /> Normalize history</label
          >
        </template>
      </div>
    </details>

    <div
      v-if="selectedCashflowItem"
      class="forecast-item-modal-overlay"
      role="presentation"
      @click.self="closeCashflowModal"
    >
      <section
        ref="cashflowDialogRef"
        class="forecast-item-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Cashflow source details"
        tabindex="-1"
      >
        <header class="forecast-item-modal__header">
          <div>
            <h3 class="forecast-item-modal__title">{{ selectedCashflowItem.label }}</h3>
            <p class="forecast-item-modal__amount">
              {{ formatSignedCurrency(selectedCashflowItem.amount) }}
            </p>
          </div>
          <button type="button" class="forecast-item-modal__close" @click="closeCashflowModal">
            Close
          </button>
        </header>

        <dl class="forecast-item-modal__meta">
          <div>
            <dt>Category</dt>
            <dd>{{ selectedCashflowItem.category || 'Uncategorized' }}</dd>
          </div>
          <div>
            <dt>Confidence</dt>
            <dd>{{ selectedCashflowItem.confidence ?? 'Unknown' }}</dd>
          </div>
          <div>
            <dt>Detected as</dt>
            <dd>{{ itemOriginLabel(selectedCashflowItem) }}</dd>
          </div>
        </dl>

        <section>
          <h4 class="forecast-item-modal__sources-title">Source transactions/events</h4>
          <p
            v-if="cashflowSources(selectedCashflowItem).length === 0"
            class="forecast-item-modal__empty"
          >
            No source transactions or events are attached to this forecast item.
          </p>
          <ul v-else class="forecast-item-modal__source-list">
            <li
              v-for="(sourceItem, index) in cashflowSources(selectedCashflowItem)"
              :key="sourceItem.id || sourceItem.transaction_id || sourceItem.event_id || index"
            >
              <p class="forecast-item-modal__source-title">
                {{
                  sourceItem.description ||
                  sourceItem.merchant ||
                  sourceItem.event ||
                  sourceItem.category_display ||
                  sourceItem.category ||
                  'Reference'
                }}
              </p>
              <p class="forecast-item-modal__source-meta">
                {{ sourceItem.date || 'Unknown date' }}
                <span v-if="sourceItem.type"> · {{ sourceItem.type }}</span>
                <span v-if="sourceItem.frequency"> · {{ sourceItem.frequency }}</span>
              </p>
              <p
                v-if="
                  sourceItem.category_display ||
                  sourceItem.category ||
                  sourceItem.category_slug ||
                  (Array.isArray(sourceItem.tags) && sourceItem.tags.length > 0)
                "
                class="forecast-item-modal__source-meta"
              >
                <span v-if="sourceItem.category_display"
                  >Category {{ sourceItem.category_display }}</span
                >
                <span v-else-if="sourceItem.category">Category {{ sourceItem.category }}</span>
                <span v-if="sourceItem.category_slug"> · Slug {{ sourceItem.category_slug }}</span>
                <span v-if="Array.isArray(sourceItem.tags) && sourceItem.tags.length > 0">
                  · Tags {{ sourceItem.tags.join(', ') }}
                </span>
              </p>
            </li>
          </ul>
        </section>
      </section>
    </div>

    <ForecastAdjustmentsForm @add-adjustment="addAdjustment" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useModalA11y } from '@/composables/useModalA11y'
import ForecastAdjustmentsForm from './ForecastAdjustmentsForm.vue'
import ForecastScenarioComparison from './ForecastScenarioComparison.vue'
import {
  type ForecastAdjustmentInput,
  type ForecastModelVersion,
  type ForecastScenarioInput,
  type ForecastCashflowItem,
  type ForecastCashflowSource,
  type ForecastGraphMode,
  type ForecastMetadata,
  type ForecastViewType,
  useForecastData,
} from '@/composables/useForecastData'
import { useAccountGroups } from '@/composables/useAccountGroups'
import api from '@/services/api'

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
  confidence?: number
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
type ForecastAspectSelection = (typeof FORECAST_ASPECT_OPTIONS)[number]['value']

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
const selectedAspect = ref<ForecastAspectSelection>('balances')
const expandedAdjustmentKeys = ref<string[]>([])

const SCENARIO_PRESETS: Array<ForecastScenarioInput> = [
  { id: 'pay-delay', label: 'Paycheck 7 days late', changes: { delay_income_days: 7 } },
  { id: 'cut-spend', label: 'Spending down 15%', changes: { residual_spending_multiplier: 0.85 } },
  { id: 'more-spend', label: 'Spending up 15%', changes: { residual_spending_multiplier: 1.15 } },
  { id: 'raise', label: 'Income up 10%', changes: { income_multiplier: 1.1 } },
]
const LOW_CASH_LINE = 500

// V2 (liquid cash) is the default. Set VITE_FORECAST_MODEL_VERSION=v1 to roll back, or pick the
// legacy model under Advanced model controls.
const modelVersion = ref<ForecastModelVersion>(
  import.meta.env.VITE_FORECAST_MODEL_VERSION === 'v1' ? 'v1' : 'v2',
)
const simulationEnabled = ref(true)
const selectedScenarioIds = ref<string[]>([])
const scenarioInputs = computed(() =>
  SCENARIO_PRESETS.filter((preset) => selectedScenarioIds.value.includes(preset.id)),
)
const cashThreshold = ref(LOW_CASH_LINE)

const forecastAspectOptions = computed(() => FORECAST_ASPECT_OPTIONS)
const { groups: accountSnapshotGroups } = useAccountGroups({ userId: userId.value })

const forecastData = useForecastData({
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
  modelVersion,
  simulationEnabled,
  scenarios: scenarioInputs,
  cashThreshold,
})
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
} = forecastData
// V2 state is optional so a V1 composable (or a test double) still works.
const appliedModelVersion = computed(() => forecastData.modelVersion?.value ?? 'v1')
const liquidity = computed(() => forecastData.liquidity?.value ?? null)
const uncertainty = computed(() => forecastData.uncertainty?.value ?? null)
const netWorth = computed(() => forecastData.netWorth?.value ?? null)
const drivers = computed(() => forecastData.drivers?.value ?? [])
const dataQuality = computed(() => forecastData.dataQuality?.value ?? null)
const debtPaymentCoverage = computed(() => forecastData.debtPaymentCoverage?.value ?? null)
const scenarioResults = computed(() => forecastData.scenarioResults?.value ?? [])
const scenarioLines = computed(() =>
  scenarioResults.value.filter((scenario) => scenario.id !== 'baseline'),
)

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
const forecastItems = computed(() => cashflows.value ?? [])
const selectedCashflowItem = ref<ForecastCashflowItem | null>(null)
const baselineTrendAdjustment = computed<ForecastAdjustmentWithMetadata | null>(() => {
  if (appliedModelVersion.value === 'v2') {
    return null
  }
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
const autoDetectedWageAdjustments = computed(() =>
  autoDetectedAdjustments.value.filter((adjustment) =>
    ['auto_income', 'auto_wage'].includes(String(adjustment.adjustment_type || '').toLowerCase()),
  ),
)
const autoDetectedRentAdjustments = computed(() =>
  autoDetectedAdjustments.value.filter(
    (adjustment) => String(adjustment.adjustment_type || '').toLowerCase() === 'auto_rent',
  ),
)
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
    modelVersion,
    simulationEnabled,
    selectedScenarioIds,
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
 * Normalize source references emitted with a forecast cashflow item.
 *
 * @param item Selected cashflow item from the breakdown list.
 * @returns Source references as a typed array.
 */
function cashflowSources(item: ForecastCashflowItem | null): ForecastCashflowSource[] {
  if (!item || !Array.isArray(item.sources)) {
    return []
  }
  return item.sources
}

/**
 * Derive a human-readable provenance label for breakdown details.
 *
 * @param item Selected forecast cashflow item.
 * @returns Source mode label used in the modal.
 */
function itemOriginLabel(item: ForecastCashflowItem | null) {
  if (!item) {
    return 'Unknown'
  }

  const source = String(item.source || '').toLowerCase()
  if (source === 'category_average') {
    return 'Historical average'
  }
  if (source === 'recurring') {
    return 'Recurring rule'
  }
  if (source === 'adjustment') {
    const adjustmentType = String(item.metadata?.adjustment_type || '').toLowerCase()
    if (adjustmentType.startsWith('auto')) {
      return 'Auto-detected'
    }
    return 'Manual adjustment'
  }
  if (source.includes('manual')) {
    return 'Manual adjustment'
  }
  if (source.includes('auto')) {
    return 'Auto-detected'
  }

  return 'Auto-detected'
}

/**
 * Open details modal for a selected forecast cashflow line item.
 *
 * @param item Cashflow entry selected in the breakdown list.
 */
function openCashflowModal(item: ForecastCashflowItem) {
  selectedCashflowItem.value = item
}

/** Close cashflow details modal. */
function closeCashflowModal() {
  selectedCashflowItem.value = null
}

const cashflowDialogRef = ref<HTMLElement | null>(null)
useModalA11y({
  dialogRef: cashflowDialogRef,
  active: computed(() => selectedCashflowItem.value !== null),
  onEscape: () => {
    closeCashflowModal()
    return true
  },
})

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
.disclosure-summary {
  cursor: pointer;
  font-weight: 600;
  min-height: var(--control-height-sm);
  display: flex;
  align-items: center;
}

.disclosure-summary:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}

@reference "../../assets/css/main.css";

/* The page layout owns the outer gutter; this component only owns vertical rhythm. */
.forecast-layout {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 0;
  color: var(--text-primary);
}

.control-row {
  display: flex;
  gap: 0.75rem 1rem;
  align-items: flex-end;
  flex-wrap: wrap;
}

.control-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.control-field__label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.control-field__input {
  width: auto;
  min-width: min(100%, 10rem);
  max-width: 100%;
}

.control-check {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  min-height: var(--control-height);
  font-size: 0.875rem;
}

.adjustments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 16.25rem), 1fr));
  gap: 1rem;
}

.adjustments-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 0.4rem;
}

.adjustments-empty {
  font-size: 0.875rem;
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
  font-size: 0.875rem;
  overflow-wrap: anywhere;
}

.adjustments-list li > strong {
  flex: none;
  font-variant-numeric: tabular-nums;
}

.source-transaction-item__description,
.source-transaction-item__meta,
.source-transaction-item__matching,
.auto-adjustment-item__label,
.auto-adjustment-item__meta {
  overflow-wrap: anywhere;
  min-width: 0;
}

.adjustments-list.auto strong {
  color: var(--text-positive);
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

.auto-adjustments-groups {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
}

.auto-adjustments-group-title {
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.4rem;
}

.auto-adjustments-list--rent .auto-adjustment-item {
  border-left: 3px solid rgba(220, 38, 38, 0.4);
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
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.auto-adjustment-item__actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.45rem;
}

.auto-adjustment-toggle {
  border: 1px solid color-mix(in srgb, var(--accent-primary) 30%, transparent);
  border-radius: 999px;
  padding: 0.35rem 0.75rem;
  background: color-mix(in srgb, var(--accent-primary) 12%, transparent);
  color: var(--text-link);
  font-size: 0.8125rem;
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
  background: var(--surface-2);
  padding: 0.75rem 0.85rem;
}

.forecast-item-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.35);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
  z-index: 50;
}

.forecast-item-modal {
  width: min(640px, 100%);
  max-height: calc(100dvh - 2rem);
  overflow: auto;
  overscroll-behavior: contain;
  background: var(--surface);
  border-radius: 0.75rem;
  border: 1px solid var(--divider);
  padding: 1rem;
  display: grid;
  gap: 1rem;
}

.forecast-item-modal__header {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
}

.forecast-item-modal__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.forecast-item-modal__amount {
  margin: 0.25rem 0 0;
  color: var(--text-muted);
}

.forecast-item-modal__close {
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 0.4rem;
  background: transparent;
  padding: 0.35rem 0.6rem;
  font-size: 0.85rem;
}

.forecast-item-modal__meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin: 0;
}

.forecast-item-modal__meta dt {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.forecast-item-modal__meta dd {
  margin: 0.2rem 0 0;
  font-size: 0.9rem;
}

.forecast-item-modal__sources-title {
  margin: 0 0 0.5rem;
  font-size: 0.92rem;
  font-weight: 600;
}

.forecast-item-modal__empty,
.forecast-item-modal__source-meta {
  margin: 0.2rem 0 0;
  font-size: 0.84rem;
  color: var(--text-muted);
}

.forecast-item-modal__source-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.65rem;
}

.forecast-item-modal__source-list li {
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 0.6rem;
  padding: 0.65rem;
}

.forecast-item-modal__source-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
}
</style>
