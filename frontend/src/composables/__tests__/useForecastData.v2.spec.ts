import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'
import {
  useForecastData,
  type ForecastModelVersion,
  type ForecastScenarioInput,
} from '@/composables/useForecastData'

const v2Response = {
  model_version: 'v2',
  status: 'ok',
  timeline: [
    {
      date: '2026-11-01',
      label: '2026-11-01',
      forecast_balance: 5000,
      liquid_cash: 5000,
      actual_balance: null,
      p10: 4800,
      p50: 5000,
      p90: 5200,
    },
  ],
  summary: { starting_balance: 5000, ending_balance: 5000, net_change: 0 },
  cashflows: [],
  adjustments: [],
  series: {},
  metadata: { balance_basis: 'liquid_cash' },
  liquidity: {
    starting_cash: 5000,
    ending_cash: 5000,
    min_cash: 4900,
    min_cash_date: '2026-11-03',
    first_shortfall_date: null,
  },
  net_worth: {
    starting: 9300,
    ending: 9300,
    liabilities: { starting: 700, ending: 700 },
    investments: { starting: 5000, ending: 5000 },
  },
  uncertainty: {
    available: true,
    risk_below_zero_any_day: 0.02,
    risk_below_threshold_any_day: 0.2,
  },
  drivers: [
    {
      event_id: 'e1',
      source_id: 's1',
      date: '2026-11-01',
      amount: -1500,
      kind: 'scheduled_bill',
      origin: 'detected_recurring',
      confidence_label: 'high',
    },
  ],
  data_quality: { as_of_date: '2026-10-31', history_days: 120, warnings: [] },
  scenarios: [{ id: 'baseline', label: 'Baseline', ending_cash: 5000 }],
}

function setup(overrides: Record<string, unknown> = {}) {
  const modelVersion = ref<ForecastModelVersion>('v2')
  const scenarios = ref<ForecastScenarioInput[]>([])
  const options = {
    viewType: ref<'Month' | 'Year'>('Month'),
    manualIncome: ref(0),
    liabilityRate: ref(0),
    adjustments: ref([]),
    userId: ref('alice'),
    includedAccountIds: ref(['chk']),
    excludedAccountIds: ref<string[]>([]),
    movingAverageWindow: ref<7 | 30 | 60 | 90>(30),
    normalize: ref(false),
    graphMode: ref<'combined' | 'forecast' | 'historical'>('combined'),
    modelVersion,
    simulationEnabled: ref(true),
    scenarios,
    cashThreshold: ref(500),
    ...overrides,
  }
  return { api: useForecastData(options), modelVersion, scenarios }
}

describe('useForecastData V2', () => {
  const originalFetch = global.fetch
  beforeEach(() => {
    global.fetch = vi.fn()
  })
  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('sends the versioned V2 request with simulation, scenarios and account scope', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => v2Response,
    })
    const { api, scenarios } = setup()
    scenarios.value = Array.from({ length: 7 }, (_, i) => ({
      id: `s${i}`,
      label: `S${i}`,
      changes: { delay_income_days: 7 },
    }))
    await api.fetchData()
    const body = JSON.parse((global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body)
    expect(body).toMatchObject({
      model_version: 'v2',
      user_id: 'alice',
      horizon_days: 30,
      included_account_ids: ['chk'],
      simulation: { enabled: true, count: 300, seed: 12345, cash_threshold: 500 },
    })
    expect(body.scenarios).toHaveLength(5)
    expect(body).not.toHaveProperty('moving_average_window')
  })

  it('maps liquidity, uncertainty, bands, drivers, data quality and scenarios', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => v2Response,
    })
    const { api } = setup()
    await api.fetchData()
    expect(api.modelVersion.value).toBe('v2')
    expect(api.liquidity.value?.min_cash).toBe(4900)
    expect(api.netWorth.value?.liabilities.starting).toBe(700)
    expect(api.uncertainty.value?.available).toBe(true)
    expect(api.timeline.value[0]).toMatchObject({ p10: 4800, p90: 5200 })
    expect(api.drivers.value[0].origin).toBe('detected_recurring')
    expect(api.dataQuality.value?.history_days).toBe(120)
    expect(api.scenarioResults.value).toHaveLength(1)
  })

  it('keeps the legacy request when no model version is provided', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({
        timeline: [],
        summary: null,
        cashflows: [],
        adjustments: [],
        series: {},
        metadata: {},
      }),
    })
    const { api } = setup({ modelVersion: undefined })
    await api.fetchData()
    const body = JSON.parse((global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body)
    expect(body.model_version).toBeUndefined()
    expect(body).toMatchObject({ moving_average_window: 30, graph_mode: 'combined' })
    expect(api.modelVersion.value).toBe('v1')
    expect(api.liquidity.value).toBeNull()
  })

  it('falls back to V1 state when the server answers a V2 request with a legacy payload', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({
        timeline: [],
        summary: null,
        cashflows: [],
        adjustments: [],
        series: {},
        metadata: {},
      }),
    })
    const { api } = setup()
    await api.fetchData()
    expect(api.modelVersion.value).toBe('v1')
    expect(api.uncertainty.value).toBeNull()
  })

  it('surfaces the server error message for rejected V2 requests', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({
        error: 'One or more requested accounts are not available to this user.',
      }),
    })
    const { api } = setup()
    await api.fetchData()
    expect(api.error.value?.message).toContain('not available to this user')
    expect(api.loading.value).toBe(false)
  })

  it('uses a generic message when the error body is unreadable', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      json: async () => {
        throw new Error('bad json')
      },
    })
    const { api } = setup()
    await api.fetchData()
    expect(api.error.value?.message).toBe('Failed to compute forecast data.')
  })

  it('lets the latest request win when responses arrive out of order', async () => {
    let releaseFirst: (_value: unknown) => void = () => {}
    const slow = new Promise((resolve) => {
      releaseFirst = resolve
    })
    const calls: Array<{ signal: AbortSignal }> = []
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockImplementationOnce((_url: string, init: { signal: AbortSignal }) => {
        calls.push(init)
        return slow
      })
      .mockImplementationOnce((_url: string, init: { signal: AbortSignal }) => {
        calls.push(init)
        return Promise.resolve({
          ok: true,
          json: async () => ({
            ...v2Response,
            liquidity: { ...v2Response.liquidity, ending_cash: 111 },
          }),
        })
      })
    const { api } = setup()
    const first = api.fetchData()
    const second = api.fetchData()
    await second
    expect(calls[0].signal.aborted).toBe(true)
    // The stale response arrives afterwards and must be ignored.
    releaseFirst({
      ok: true,
      json: async () => ({
        ...v2Response,
        liquidity: { ...v2Response.liquidity, ending_cash: 999 },
      }),
    })
    await first
    await nextTick()
    expect(api.liquidity.value?.ending_cash).toBe(111)
    expect(api.loading.value).toBe(false)
    expect(api.error.value).toBeNull()
  })

  it('ignores aborted requests without surfacing an error', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockRejectedValueOnce(Object.assign(new Error('aborted'), { name: 'AbortError' }))
      .mockResolvedValueOnce({ ok: true, json: async () => v2Response })
    const { api } = setup()
    const first = api.fetchData()
    const second = api.fetchData()
    await Promise.all([first, second])
    expect(api.error.value).toBeNull()
    expect(api.liquidity.value?.starting_cash).toBe(5000)
  })
})
