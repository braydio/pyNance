import { computed, ref, type Ref } from 'vue'

export type ForecastViewType = 'Month' | 'Year'
export type ForecastGraphMode = 'combined' | 'forecast' | 'historical'
export type ForecastSeriesId =
  | 'realized_income'
  | 'manual_adjustments'
  | 'spending'
  | 'debt_totals'
  | 'debt_interest'
  | 'debt_new_spending'

export type ForecastAdjustmentInput = {
  label: string
  amount: number
  date?: string
  frequency?: 'daily' | 'weekly' | 'monthly' | null
  adjustment_type?: string
  reason?: string
  distribution?: 'single' | 'spread'
  range_start?: string
  range_end?: string
  metadata?: ForecastMetadata
}

export type ForecastMetadata = {
  asset_balance?: number
  liability_balance?: number
  net_balance?: number
  lookback_days?: number
  realized_history_lookback_days?: number
  moving_average_window?: number
  normalize?: boolean
  graph_mode?: ForecastGraphMode
  projected_amount?: number
  projected_change?: number
  projected_change_percent?: number
  realized_history?: ForecastRealizedHistoryPoint[]
  [key: string]: unknown
}

export type ForecastTimelinePoint = {
  date: string
  label: string
  forecast_balance: number
  actual_balance: number | null
  delta?: number | null
  metadata?: ForecastMetadata
}

export type ForecastSummary = {
  start_date: string
  end_date: string
  starting_balance: number
  ending_balance: number
  net_change: number
  total_inflows: number
  total_outflows: number
  average_daily_change: number
  min_balance: number
  max_balance: number
  depletion_date?: string | null
  currency?: string
  breakdowns?: Record<string, number>
  account_count?: number | null
  recurring_count?: number | null
  metadata?: ForecastMetadata
}

export type ForecastCashflowItem = {
  date: string
  amount: number
  label: string
  category: string
  source: string
  type?: string | null
  confidence?: number | null
  account_id?: number | null
  recurring_id?: number | null
  direction?: string | null
  sources?: ForecastCashflowSource[] | null
  metadata?: ForecastMetadata
}

export type ForecastCashflowSource = {
  type?: string
  id?: string
  transaction_id?: string
  recurring_id?: string | number
  account_id?: string | number
  date?: string
  description?: string
  merchant?: string
  event?: string
  event_id?: string
  event_type?: string
  frequency?: string
  category?: string
  category_display?: string
  category_slug?: string
  tags?: string[]
  [key: string]: unknown
}

export type ForecastSeriesPoint = {
  date: string
  label: string
  value: number
  metadata?: ForecastMetadata
}

export type ForecastAspectSeries = {
  id: ForecastSeriesId
  label: string
  points: ForecastSeriesPoint[]
  metadata?: ForecastMetadata
}

export type ForecastSeriesMap = Partial<Record<ForecastSeriesId, ForecastAspectSeries>>

export type ForecastRealizedHistoryPoint = {
  date: string
  label: string
  balance: number
}

type ForecastComputeResponse = {
  timeline: ForecastTimelinePoint[]
  summary: ForecastSummary | null
  cashflows: ForecastCashflowItem[]
  adjustments: ForecastAdjustmentInput[]
  series: ForecastSeriesMap
  metadata: ForecastMetadata
}

export type UseForecastDataOptions = {
  viewType: Ref<ForecastViewType>
  manualIncome: Ref<number>
  liabilityRate: Ref<number>
  adjustments: Ref<ForecastAdjustmentInput[]>
  userId: Ref<string>
  includedAccountIds: Ref<string[]>
  excludedAccountIds: Ref<string[]>
  movingAverageWindow: Ref<7 | 30 | 60 | 90>
  normalize: Ref<boolean>
  graphMode: Ref<ForecastGraphMode>
}

function isSeriesMap(value: unknown): value is ForecastSeriesMap {
  return Boolean(value) && typeof value === 'object'
}

/**
 * Fetch forecast data from the compute endpoint and expose reactive state.
 */
export function useForecastData({
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
}: UseForecastDataOptions) {
  const timeline = ref<ForecastTimelinePoint[]>([])
  const summary = ref<ForecastSummary | null>(null)
  const cashflows = ref<ForecastCashflowItem[]>([])
  const appliedAdjustments = ref<ForecastAdjustmentInput[]>([])
  const series = ref<ForecastSeriesMap>({})
  const metadata = ref<ForecastMetadata>({})
  const loading = ref(false)
  const error = ref<Error | null>(null)

  /**
   * Convert a Date to an ISO date string (YYYY-MM-DD).
   */
  const formatDate = (value: Date) => value.toISOString().split('T')[0]

  /**
   * Build a payload that aligns manual inputs with compute adjustments.
   */
  const buildAdjustments = (startDate: string) => {
    const entries = adjustments.value.map((adjustment) => ({
      ...adjustment,
      date: adjustment.date ?? startDate,
      adjustment_type: adjustment.adjustment_type ?? 'manual',
    }))

    const manualEntries: ForecastAdjustmentInput[] = []
    if (manualIncome.value) {
      manualEntries.push({
        label: 'Manual income',
        amount: manualIncome.value,
        date: startDate,
        frequency: 'daily',
        adjustment_type: 'manual',
      })
    }
    if (liabilityRate.value) {
      manualEntries.push({
        label: 'Liability rate',
        amount: -Math.abs(liabilityRate.value),
        date: startDate,
        frequency: 'daily',
        adjustment_type: 'manual',
      })
    }

    return [...entries, ...manualEntries].filter((entry) => entry.amount !== 0)
  }

  /**
   * Build account include/exclude lists for compute requests.
   */
  const buildAccountFilters = () => ({
    included_account_ids: [...includedAccountIds.value],
    excluded_account_ids: [...excludedAccountIds.value],
  })

  const fetchData = async () => {
    loading.value = true
    error.value = null
    try {
      if (!userId.value) {
        timeline.value = []
        summary.value = null
        cashflows.value = []
        appliedAdjustments.value = []
        series.value = {}
        metadata.value = {}
        throw new Error('Forecast user_id is not configured.')
      }

      const startDate = formatDate(new Date())
      const horizonDays = viewType.value === 'Year' ? 365 : 30
      const adjustmentPayload = buildAdjustments(startDate)

      const res = await fetch('/api/forecast/compute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId.value,
          start_date: startDate,
          horizon_days: horizonDays,
          adjustments: adjustmentPayload,
          moving_average_window: movingAverageWindow.value,
          normalize: normalize.value,
          graph_mode: graphMode.value,
          ...buildAccountFilters(),
        }),
      })

      if (!res.ok) {
        throw new Error('Failed to compute forecast data.')
      }

      const data: ForecastComputeResponse = await res.json()
      timeline.value = Array.isArray(data.timeline) ? data.timeline : []
      summary.value = data.summary ?? null
      cashflows.value = Array.isArray(data.cashflows) ? data.cashflows : []
      appliedAdjustments.value = Array.isArray(data.adjustments) ? data.adjustments : []
      series.value = isSeriesMap(data.series) ? data.series : {}
      metadata.value = data?.metadata && typeof data.metadata === 'object' ? data.metadata : {}
    } catch (err) {
      error.value = err as Error
    } finally {
      loading.value = false
    }
  }

  return {
    timeline: computed(() => timeline.value),
    summary: computed(() => summary.value),
    cashflows: computed(() => cashflows.value),
    adjustments: computed(() => appliedAdjustments.value),
    series: computed(() => series.value),
    metadata: computed(() => metadata.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    fetchData,
  }
}
