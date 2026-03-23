import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useForecastData } from '@/composables/useForecastData'

describe('useForecastData', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    global.fetch = vi.fn()
  })

  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('posts account filters and adjustments to the compute endpoint and maps response data', async () => {
    const viewType = ref<'Month' | 'Year'>('Month')
    const manualIncome = ref(150)
    const liabilityRate = ref(20)
    const adjustments = ref([
      {
        label: 'Manual bonus',
        amount: 200,
        frequency: 'monthly' as const,
      },
    ])
    const userId = ref('user-123')
    const includedAccountIds = ref(['acc-1', 'acc-2'])
    const excludedAccountIds = ref(['acc-3'])
    const movingAverageWindow = ref<7 | 30 | 60 | 90>(30)
    const normalize = ref(false)
    const graphMode = ref<'combined' | 'forecast' | 'historical'>('combined')

    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({
        timeline: [
          {
            date: '2024-01-01',
            label: 'Jan 1',
            forecast_balance: 100,
            actual_balance: 90,
          },
        ],
        summary: {
          starting_balance: 100,
          ending_balance: 110,
          net_change: 10,
        },
        cashflows: [{ label: 'Manual bonus', amount: 200 }],
        adjustments: [],
        series: {
          manual_adjustments: {
            id: 'manual_adjustments',
            label: 'Manual adjustments',
            points: [{ date: '2024-01-01', label: '2024-01-01', value: 200 }],
          },
        },
        metadata: {
          included_account_ids: ['acc-1', 'acc-2'],
          excluded_account_ids: ['acc-3'],
        },
      }),
    })

    const { fetchData, timeline, cashflows, series } = useForecastData({
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

    await fetchData()
    await nextTick()

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/forecast/compute',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const callBody = JSON.parse((global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body)

    expect(callBody).toMatchObject({
      user_id: 'user-123',
      horizon_days: 30,
      moving_average_window: 30,
      normalize: false,
      graph_mode: 'combined',
      included_account_ids: ['acc-1', 'acc-2'],
      excluded_account_ids: ['acc-3'],
    })
    expect(callBody.adjustments).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ label: 'Manual bonus', amount: 200, frequency: 'monthly' }),
        expect.objectContaining({ label: 'Manual income', amount: 150, frequency: 'daily' }),
        expect.objectContaining({ label: 'Liability rate', amount: -20, frequency: 'daily' }),
      ]),
    )

    expect(timeline.value).toHaveLength(1)
    expect(cashflows.value).toEqual([{ label: 'Manual bonus', amount: 200 }])
    expect(series.value.manual_adjustments?.points).toEqual([
      { date: '2024-01-01', label: '2024-01-01', value: 200 },
    ])
  })

  it('returns an error when userId is missing', async () => {
    const viewType = ref<'Month' | 'Year'>('Month')
    const manualIncome = ref(0)
    const liabilityRate = ref(0)
    const adjustments = ref([])
    const userId = ref('')
    const includedAccountIds = ref([])
    const excludedAccountIds = ref([])

    const { fetchData, error, timeline } = useForecastData({
      viewType,
      manualIncome,
      liabilityRate,
      adjustments,
      userId,
      includedAccountIds,
      excludedAccountIds,
      movingAverageWindow: ref<7 | 30 | 60 | 90>(30),
      normalize: ref(false),
      graphMode: ref<'combined' | 'forecast' | 'historical'>('combined'),
    })

    await fetchData()
    await nextTick()

    expect(error.value).toBeTruthy()
    expect(timeline.value).toEqual([])
  })
})
