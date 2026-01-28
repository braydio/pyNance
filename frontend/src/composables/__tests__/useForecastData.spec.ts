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

  it('posts adjustments to the compute endpoint and maps response data', async () => {
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
        metadata: {},
      }),
    })

    const { fetchData, timeline, cashflows } = useForecastData({
      viewType,
      manualIncome,
      liabilityRate,
      adjustments,
      userId,
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
  })

  it('returns an error when userId is missing', async () => {
    const viewType = ref<'Month' | 'Year'>('Month')
    const manualIncome = ref(0)
    const liabilityRate = ref(0)
    const adjustments = ref([])
    const userId = ref('')

    const { fetchData, error, timeline } = useForecastData({
      viewType,
      manualIncome,
      liabilityRate,
      adjustments,
      userId,
    })

    await fetchData()
    await nextTick()

    expect(error.value).toBeTruthy()
    expect(timeline.value).toEqual([])
  })
})
