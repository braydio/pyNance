import { computed, ref, type Ref } from 'vue'

export type ForecastViewType = 'Month' | 'Quarter' | 'Year'
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

export type ForecastModelVersion = 'v1' | 'v2'

export type ForecastTimelinePoint = {
  date: string
  label: string
  /** V2: liquid cash (checking/savings/cash only), never net worth. */
  forecast_balance: number
  actual_balance: number | null
  delta?: number | null
  metadata?: ForecastMetadata
  /** V2 only. Present when a simulation produced bands; never fabricated otherwise. */
  liquid_cash?: number
  p10?: number
  p50?: number
  p90?: number
  events?: string[]
}

export type ForecastLiquidity = {
  starting_cash: number
  ending_cash: number
  min_cash: number
  min_cash_date: string
  first_shortfall_date: string | null
}

export type ForecastUncertainty = {
  available: boolean
  reason?: string | null
  risk_below_zero_any_day?: number
  risk_below_threshold_any_day?: number
  threshold?: number
  sample_count?: number
  seed?: number
  interval?: string
}

export type ForecastNetWorth = {
  starting: number
  ending: number
  liabilities: { starting: number; ending: number }
  investments: { starting: number; ending: number }
}

export type ForecastDriver = {
  event_id: string
  source_id: string | null
  date: string
  amount: number
  kind: string
  origin: string
  confidence_label: 'high' | 'medium' | 'low' | string
  label?: string | null
  account_id?: string | null
}

export type ForecastDataQuality = {
  as_of_date: string
  history_days: number
  confidence?: string
  residual_model?: string
  proposed_streams?: number
  warnings: Array<{ code: string; message: string; [key: string]: unknown }>
}

export type ForecastScenarioChanges = {
  residual_spending_multiplier?: number
  income_multiplier?: number
  delay_income_days?: number
  adjustments?: ForecastAdjustmentInput[]
}

export type ForecastScenarioInput = {
  id: string
  label: string
  changes: ForecastScenarioChanges
}

export type ForecastScenarioResult = {
  id: string
  label: string
  ending_cash: number
  min_cash: number
  min_cash_date: string
  first_shortfall_date: string | null
  delta_vs_baseline: { ending_cash: number; min_cash: number }
  timeline: Array<{ date: string; liquid_cash: number }>
  risk: {
    probability_cash_below_zero_any_day: number
    probability_cash_below_threshold_any_day: number
    delta_vs_baseline: {
      probability_cash_below_zero_any_day: number
      probability_cash_below_threshold_any_day: number
    } | null
  } | null
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
  model_version?: ForecastModelVersion
  status?: string
  liquidity?: ForecastLiquidity | null
  net_worth?: ForecastNetWorth | null
  uncertainty?: ForecastUncertainty
  drivers?: ForecastDriver[]
  data_quality?: ForecastDataQuality
  scenarios?: ForecastScenarioResult[]
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
  /** Defaults to 'v1' so existing callers keep the legacy request/response. */
  modelVersion?: Readonly<Ref<ForecastModelVersion>>
  /** V2 only: request P10/P50/P90 bands and shortfall risk. */
  simulationEnabled?: Readonly<Ref<boolean>>
  /** V2 only: request-local what-if scenarios (max 5). */
  scenarios?: Readonly<Ref<ForecastScenarioInput[]>>
  /** V2 only: cash floor used for the low-cash probability. */
  cashThreshold?: Readonly<Ref<number>>
}

const SIMULATION_COUNT = 300
const SIMULATION_SEED = 12345

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
  modelVersion,
  simulationEnabled,
  scenarios,
  cashThreshold,
}: UseForecastDataOptions) {
  const timeline = ref<ForecastTimelinePoint[]>([])
  const summary = ref<ForecastSummary | null>(null)
  const cashflows = ref<ForecastCashflowItem[]>([])
  const appliedAdjustments = ref<ForecastAdjustmentInput[]>([])
  const series = ref<ForecastSeriesMap>({})
  const metadata = ref<ForecastMetadata>({})
  const loading = ref(false)
  const error = ref<Error | null>(null)
  const appliedModelVersion = ref<ForecastModelVersion>('v1')
  const liquidity = ref<ForecastLiquidity | null>(null)
  const netWorth = ref<ForecastNetWorth | null>(null)
  const uncertainty = ref<ForecastUncertainty | null>(null)
  const drivers = ref<ForecastDriver[]>([])
  const dataQuality = ref<ForecastDataQuality | null>(null)
  const scenarioResults = ref<ForecastScenarioResult[]>([])

  // Latest request wins: an older response must never overwrite a newer scope/scenario.
  let requestSeq = 0
  let inFlight: AbortController | null = null

  const resetV2State = () => {
    appliedModelVersion.value = 'v1'
    liquidity.value = null
    netWorth.value = null
    uncertainty.value = null
    drivers.value = []
    dataQuality.value = null
    scenarioResults.value = []
  }

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

  const buildRequestBody = (
    startDate: string,
    horizonDays: number,
    version: ForecastModelVersion,
  ) => {
    const base = {
      user_id: userId.value,
      start_date: startDate,
      horizon_days: horizonDays,
      adjustments: buildAdjustments(startDate),
      ...buildAccountFilters(),
    }
    if (version === 'v2') {
      return {
        ...base,
        model_version: 'v2',
        scenarios: (scenarios?.value ?? []).slice(0, 5),
        simulation: {
          enabled: Boolean(simulationEnabled?.value),
          count: SIMULATION_COUNT,
          seed: SIMULATION_SEED,
          cash_threshold: Math.max(0, Number(cashThreshold?.value ?? 0)),
        },
      }
    }
    return {
      ...base,
      moving_average_window: movingAverageWindow.value,
      normalize: normalize.value,
      graph_mode: graphMode.value,
    }
  }

  const fetchData = async () => {
    const seq = ++requestSeq
    inFlight?.abort()
    const controller = new AbortController()
    inFlight = controller
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
        resetV2State()
        throw new Error('Forecast user_id is not configured.')
      }

      const version: ForecastModelVersion = modelVersion?.value === 'v2' ? 'v2' : 'v1'
      const startDate = formatDate(new Date())
      const horizonDays = viewType.value === 'Year' ? 365 : viewType.value === 'Quarter' ? 90 : 30

      const res = await fetch('/api/forecast/compute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildRequestBody(startDate, horizonDays, version)),
        signal: controller.signal,
      })

      if (!res.ok) {
        let failure: { error?: unknown } | null = null
        try {
          failure = await res.json()
        } catch {
          failure = null
        }
        throw new Error(
          typeof failure?.error === 'string' ? failure.error : 'Failed to compute forecast data.',
        )
      }

      const data: ForecastComputeResponse = await res.json()
      if (seq !== requestSeq) return
      timeline.value = Array.isArray(data.timeline) ? data.timeline : []
      summary.value = data.summary ?? null
      cashflows.value = Array.isArray(data.cashflows) ? data.cashflows : []
      appliedAdjustments.value = Array.isArray(data.adjustments) ? data.adjustments : []
      series.value = isSeriesMap(data.series) ? data.series : {}
      metadata.value = data?.metadata && typeof data.metadata === 'object' ? data.metadata : {}
      if (version === 'v2' && data.model_version === 'v2') {
        appliedModelVersion.value = 'v2'
        liquidity.value = data.liquidity ?? null
        netWorth.value = data.net_worth ?? null
        uncertainty.value = data.uncertainty ?? { available: false }
        drivers.value = Array.isArray(data.drivers) ? data.drivers : []
        dataQuality.value = data.data_quality ?? null
        scenarioResults.value = Array.isArray(data.scenarios) ? data.scenarios : []
      } else {
        resetV2State()
      }
    } catch (err) {
      if (seq !== requestSeq || (err as Error)?.name === 'AbortError') return
      error.value = err as Error
    } finally {
      if (seq === requestSeq) {
        loading.value = false
        inFlight = null
      }
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
    modelVersion: computed(() => appliedModelVersion.value),
    liquidity: computed(() => liquidity.value),
    netWorth: computed(() => netWorth.value),
    uncertainty: computed(() => uncertainty.value),
    drivers: computed(() => drivers.value),
    dataQuality: computed(() => dataQuality.value),
    scenarioResults: computed(() => scenarioResults.value),
    fetchData,
  }
}
