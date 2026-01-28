// src/composables/useForecastData.ts

import { ref, computed, type Ref } from 'vue'

export type ForecastViewType = 'Month' | 'Year'

export type ForecastAdjustmentInput = {
  label: string
  amount: number
  date?: string
  frequency?: 'daily' | 'weekly' | 'monthly' | null
  adjustment_type?: string
  reason?: string
}

export type ForecastTimelinePoint = {
  date: string
  label: string
  forecast_balance: number
  actual_balance: number | null
  delta?: number | null
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
  metadata?: Record<string, unknown>
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
  metadata?: Record<string, unknown>
}

type ForecastComputeResponse = {
  timeline: ForecastTimelinePoint[]
  summary: ForecastSummary | null
  cashflows: ForecastCashflowItem[]
  adjustments: ForecastAdjustmentInput[]
  metadata: Record<string, unknown>
}

type UseForecastDataOptions = {
  viewType: Ref<ForecastViewType>
  manualIncome: Ref<number>
  liabilityRate: Ref<number>
  adjustments: Ref<ForecastAdjustmentInput[]>
  userId: Ref<string>
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
}: UseForecastDataOptions) {
  const timeline = ref<ForecastTimelinePoint[]>([])
  const summary = ref<ForecastSummary | null>(null)
  const cashflows = ref<ForecastCashflowItem[]>([])
  const appliedAdjustments = ref<ForecastAdjustmentInput[]>([])
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

  const fetchData = async () => {
    loading.value = true
    error.value = null
    try {
      if (!userId.value) {
        timeline.value = []
        summary.value = null
        cashflows.value = []
        appliedAdjustments.value = []
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
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    fetchData,
  }
}
