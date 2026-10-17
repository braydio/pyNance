// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ForecastBreakdown from '../ForecastBreakdown.vue'
import ForecastChart from '../ForecastChart.vue'
import ForecastScenarioComparison from '../ForecastScenarioComparison.vue'
import ForecastSummaryPanel from '../ForecastSummaryPanel.vue'

const { chartConstructor } = vi.hoisted(() => ({
  chartConstructor: vi.fn().mockImplementation(() => ({ destroy: vi.fn() })),
}))

vi.mock('chart.js', () => ({
  Chart: Object.assign(chartConstructor, { register: vi.fn() }),
  LineController: {},
  LineElement: {},
  BarController: {},
  BarElement: {},
  CategoryScale: {},
  LinearScale: {},
  PointElement: {},
  Legend: {},
  Tooltip: {},
  Filler: {},
}))

const liquidity = {
  starting_cash: 5000,
  ending_cash: 3200.5,
  min_cash: 1200,
  min_cash_date: '2026-11-20',
  first_shortfall_date: null,
}
const netWorth = {
  starting: 9300,
  ending: 9000,
  liabilities: { starting: 700, ending: 700 },
  investments: { starting: 5000, ending: 5000 },
}
const summaryBase = {
  assetBalance: 0,
  liabilityBalance: 0,
  netBalance: 0,
  manualIncome: 0,
  liabilityRate: 0,
  viewType: 'Month',
  includedAccountIds: ['chk'],
  excludedAccountIds: [],
  accountOptions: [{ account_id: 'chk', name: 'Checking' }],
}

describe('ForecastSummaryPanel (V2)', () => {
  it('leads with liquid-cash outcomes and keeps debt/investments separate', () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        ...summaryBase,
        modelVersion: 'v2',
        liquidity,
        netWorth,
        uncertainty: {
          available: true,
          risk_below_zero_any_day: 0.02,
          risk_below_threshold_any_day: 0.21,
          threshold: 500,
          sample_count: 300,
        },
      },
    })
    expect(wrapper.get('[data-testid="cash-today"]').text()).toBe('$5,000.00')
    expect(wrapper.get('[data-testid="cash-end"]').text()).toBe('$3,200.50')
    expect(wrapper.get('[data-testid="cash-min"]').text()).toContain('$1,200.00')
    expect(wrapper.get('[data-testid="cash-min"]').text()).toContain('2026-11-20')
    expect(wrapper.get('[data-testid="shortfall"]').text()).toBe('No shortfall projected')
    expect(wrapper.get('[data-testid="risk-copy"]').text()).toContain('2%')
    expect(wrapper.get('[data-testid="risk-copy"]').text()).toContain('21%')
    expect(wrapper.get('[data-testid="risk-copy"]').text()).toContain('not a guarantee')
    expect(wrapper.get('[data-testid="debt-outstanding"]').text()).toContain(
      'Outstanding debt tracked separately: $700.00',
    )
    const note = wrapper.get('[data-testid="net-worth-note"]').text()
    expect(note).toContain('Investments $5,000.00')
    expect(note).toContain('not part of this cash forecast')
    expect(wrapper.text()).not.toContain('Current Balance')
  })

  it('states the shortfall date when cash runs out', () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        ...summaryBase,
        modelVersion: 'v2',
        liquidity: { ...liquidity, first_shortfall_date: '2026-12-02' },
      },
    })
    expect(wrapper.get('[data-testid="shortfall"]').text()).toContain('2026-12-02')
  })

  it.each([
    ['simulation_disabled', 'turned off'],
    ['insufficient_history: 2 complete weeks, need 4', 'Not enough clean history'],
    ['no_liquid_cash_accounts', 'not available'],
  ])('explains unavailable uncertainty (%s) without showing percentages', (reason, copy) => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        ...summaryBase,
        modelVersion: 'v2',
        liquidity,
        uncertainty: { available: false, reason },
      },
    })
    expect(wrapper.find('[data-testid="risk-copy"]').exists()).toBe(false)
    expect(wrapper.get('[data-testid="risk-unavailable"]').text()).toContain(copy)
    expect(wrapper.text()).not.toContain('%')
  })

  it('keeps the legacy Assets/Liabilities/Current Balance fields for V1', () => {
    const wrapper = mount(ForecastSummaryPanel, { props: { ...summaryBase, assetBalance: 900 } })
    expect(wrapper.find('[data-testid="liquidity-summary"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Current Balance')
  })
})

describe('ForecastBreakdown (V2)', () => {
  const drivers = [
    {
      event_id: 'e1',
      source_id: 's1',
      date: '2026-11-01',
      amount: -1500,
      kind: 'scheduled_bill',
      origin: 'detected_recurring',
      confidence_label: 'high',
      label: 'landlord properties',
    },
    {
      event_id: 'e2',
      source_id: 's2',
      date: '2026-11-06',
      amount: 2000,
      kind: 'scheduled_income',
      origin: 'manual_rule',
      confidence_label: 'high',
    },
  ]

  it('lists scheduled events with provenance and data-quality caveats', () => {
    const wrapper = mount(ForecastBreakdown, {
      props: {
        forecastItems: [],
        viewType: 'Month',
        modelVersion: 'v2',
        drivers,
        dataQuality: {
          as_of_date: '2026-10-31',
          history_days: 120,
          confidence: 'high',
          proposed_streams: 1,
          warnings: [{ code: 'stale_snapshot', message: 'Balance is 5 days old' }],
        },
      },
    })
    const rows = wrapper.findAll('.driver-row')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('landlord properties')
    expect(rows[0].text()).toContain('Detected pattern')
    expect(rows[0].text()).toContain('\u2212$1,500.00')
    expect(rows[1].text()).toContain('Your rule')
    expect(rows[1].text()).toContain('+$2,000.00')
    const quality = wrapper.get('[data-testid="data-quality"]').text()
    expect(quality).toContain('120 days of history up to 2026-10-31')
    expect(quality).toContain('Balance is 5 days old')
    expect(quality).toContain('1 possible recurring')
    expect(wrapper.get('[data-testid="forecast-drivers"]').attributes('open')).toBeUndefined()
  })

  it('does not render the drivers section for V1', () => {
    const wrapper = mount(ForecastBreakdown, { props: { forecastItems: [], viewType: 'Month' } })
    expect(wrapper.find('[data-testid="forecast-drivers"]').exists()).toBe(false)
  })
})

describe('ForecastScenarioComparison', () => {
  const presets = [
    { id: 'pay-delay', label: 'Paycheck 7 days late' },
    { id: 'cut', label: 'Spending down 15%' },
  ]
  const results = [
    {
      id: 'baseline',
      label: 'Baseline',
      ending_cash: 3000,
      min_cash: 1000,
      min_cash_date: '2026-11-03',
      first_shortfall_date: null,
      delta_vs_baseline: { ending_cash: 0, min_cash: 0 },
      timeline: [],
      risk: null,
    },
    {
      id: 'pay-delay',
      label: 'Paycheck 7 days late',
      ending_cash: 1000,
      min_cash: -200,
      min_cash_date: '2026-11-10',
      first_shortfall_date: '2026-11-10',
      delta_vs_baseline: { ending_cash: -2000, min_cash: -1200 },
      timeline: [],
      risk: {
        probability_cash_below_zero_any_day: 0.4,
        probability_cash_below_threshold_any_day: 0.6,
        delta_vs_baseline: null,
      },
    },
  ]

  it('toggles scenarios through accessible checkboxes and respects the maximum', async () => {
    const wrapper = mount(ForecastScenarioComparison, {
      props: { presets, selectedIds: ['cut'], maxSelected: 1 },
    })
    const boxes = wrapper.findAll('input[type="checkbox"]')
    expect(boxes[0].attributes('disabled')).toBeDefined() // maximum reached
    expect(boxes[1].attributes('disabled')).toBeUndefined()
    await boxes[1].setValue(false)
    expect(wrapper.emitted('update:selectedIds')?.[0]).toEqual([[]])
    expect(wrapper.find('fieldset legend').exists()).toBe(true)
  })

  it('shows an explanatory empty state until a scenario is chosen', () => {
    const wrapper = mount(ForecastScenarioComparison, { props: { presets, selectedIds: [] } })
    expect(wrapper.get('[data-testid="scenario-empty"]').text()).toContain('not saved')
    expect(wrapper.find('table').exists()).toBe(false)
  })

  it('compares each scenario with the baseline using replayed deltas and risk', () => {
    const wrapper = mount(ForecastScenarioComparison, {
      props: { presets, selectedIds: ['pay-delay'], results },
    })
    const base = wrapper.get('[data-testid="scenario-row-baseline"]').text()
    expect(base).toContain('$3,000.00')
    const late = wrapper.get('[data-testid="scenario-row-pay-delay"]').text()
    expect(late).toContain('-$2,000.00')
    expect(late).toContain('2026-11-10')
    expect(late).toContain('40%')
    expect(wrapper.get('[role="region"]').attributes('tabindex')).toBe('0')
  })
})

describe('ForecastChart (V2)', () => {
  beforeEach(() => {
    chartConstructor.mockClear()
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(
      {} as CanvasRenderingContext2D,
    )
  })

  const point = (day: string, extra = {}) => ({
    date: day,
    label: day,
    forecast_balance: 100,
    actual_balance: null,
    ...extra,
  })

  it('adds the P10-P90 envelope, median and scenario overlays only when supported', () => {
    mount(ForecastChart, {
      props: {
        modelVersion: 'v2',
        timeline: [
          point('2026-11-01', { p10: 80, p50: 100, p90: 120 }),
          point('2026-11-02', { p10: 70, p50: 95, p90: 130 }),
        ],
        scenarioLines: [
          {
            id: 's',
            label: 'Late pay',
            timeline: [
              { date: '2026-11-01', liquid_cash: 90 },
              { date: '2026-11-02', liquid_cash: 60 },
            ],
          },
        ],
      },
    })
    const config = chartConstructor.mock.calls[0][1]
    const labels = config.data.datasets.map((d: { label: string }) => d.label)
    expect(labels).toEqual(
      expect.arrayContaining([
        'P90 (high cash)',
        'P10-P90 range',
        'Median (P50)',
        'Liquid cash forecast',
        'Late pay',
      ]),
    )
    const range = config.data.datasets.find((d: { label: string }) => d.label === 'P10-P90 range')
    expect(range.fill).toBe('-1')
    expect(range.data).toEqual([80, 70])
    expect(config.options.scales.yBalance.title.text).toBe('Liquid cash')
  })

  it('shows no band datasets without simulation output', () => {
    mount(ForecastChart, {
      props: { modelVersion: 'v2', timeline: [point('2026-11-01'), point('2026-11-02')] },
    })
    const labels = chartConstructor.mock.calls[0][1].data.datasets.map(
      (d: { label: string }) => d.label,
    )
    expect(labels).toContain('Liquid cash forecast')
    expect(labels.some((l: string) => l.includes('P10') || l.includes('P50'))).toBe(false)
  })

  it('keeps the V1 chart unchanged', () => {
    mount(ForecastChart, {
      props: {
        timeline: [point('2026-11-01')],
        realizedHistory: [{ date: '2026-10-31', label: 'x', balance: 90 }],
      },
    })
    const config = chartConstructor.mock.calls[0][1]
    expect(config.data.datasets.map((d: { label: string }) => d.label)).toEqual([
      'Historical balance',
      'Forecast balance',
    ])
    expect(config.options.scales.yBalance.title.text).toBe('Balance')
  })
})
