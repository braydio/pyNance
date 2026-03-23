// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { beforeAll, describe, expect, it, vi } from 'vitest'
import ForecastChart from '../ForecastChart.vue'
import { Chart } from 'chart.js'

const { chartConstructor, chartDestroySpy } = vi.hoisted(() => {
  const destroySpy = vi.fn()
  const constructor = vi.fn().mockImplementation(() => ({ destroy: destroySpy }))
  return {
    chartConstructor: constructor,
    chartDestroySpy: destroySpy,
  }
})

vi.mock('chart.js', () => ({
  Chart: Object.assign(
    vi.fn().mockImplementation(() => ({ destroy: vi.fn() })),
    { register: vi.fn() },
  ),
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
  Chart: Object.assign(chartConstructor, { register: vi.fn() }),
  registerables: [],
}))

describe('ForecastChart graph modes', () => {
  beforeEach(() => {
    chartConstructor.mockClear()
    chartDestroySpy.mockClear()
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({}))
  })

  it('renders balance history and forecast datasets in combined mode', () => {
    const wrapper = mount(ForecastChart, {
      props: {
        viewType: 'Month',
        graphMode: 'combined',
        selectedAspect: 'balances',
        realizedHistory: [{ label: '2026-03-20', balance: 90 }],
        timeline: [{ label: '2026-03-22', forecast_balance: 100, actual_balance: null }],
      },
    })

    expect(wrapper.text()).toContain('Month · Balances')
    expect(wrapper.find('canvas').exists()).toBe(true)
    expect(chartConstructor).toHaveBeenCalledTimes(1)
    expect(chartConstructor.mock.calls[0][1].data.datasets).toEqual([
      expect.objectContaining({
        label: 'Historical balance',
        data: [90, null],
      }),
      expect.objectContaining({
        label: 'Projected balance',
        data: [null, 100],
      }),
    ])
  })

  it('respects graph mode for the balance overlay', () => {
    mount(ForecastChart, {
      props: {
        viewType: 'Month',
        graphMode: 'historical',
        selectedAspect: 'balances',
        realizedHistory: [{ label: '2026-03-20', balance: 90 }],
        timeline: [{ label: '2026-03-22', forecast_balance: 100, actual_balance: null }],
      },
    })

    expect(chartConstructor.mock.calls[0][1].data.datasets).toEqual([
      expect.objectContaining({
        label: 'Historical balance',
        data: [90, null],
      }),
    ])
  })

  it('keeps income visible when graph mode changes away from combined', () => {
    mount(ForecastChart, {
      props: {
        viewType: 'Year',
        graphMode: 'historical',
        selectedAspect: 'realized_income',
        realizedHistory: [{ label: '2026-03-20', balance: 90 }],
        timeline: [
          { label: '2026-03-22', forecast_balance: 100, actual_balance: null },
          { label: '2026-03-23', forecast_balance: 110, actual_balance: null },
        ],
        cashflows: [
          {
            date: '2026-03-22',
            amount: 125,
            label: 'Paycheck',
            category: 'Income',
            source: 'recurring',
          },
          {
            date: '2026-03-22',
            amount: 20,
            label: 'Bonus',
            category: 'Income',
            source: 'category_average',
          },
          {
            date: '2026-03-23',
            amount: -40,
            label: 'Groceries',
            category: 'Food',
            source: 'recurring',
          },
          {
            date: '2026-03-23',
            amount: 75,
            label: 'Manual income',
            category: 'Adjustment',
            source: 'adjustment',
          },
        ],
      },
    })

    expect(chartConstructor).toHaveBeenCalledTimes(1)
    expect(chartConstructor.mock.calls[0][1].data.datasets).toEqual([
      expect.objectContaining({
        label: 'Projected income',
        data: [null, 145, null],
      }),
    ])
  })

  it('shows debt composition datasets with clear labels', () => {
    const wrapper = mount(ForecastChart, {
      props: {
        viewType: 'Month',
        graphMode: 'combined',
        selectedAspect: 'debt',
        realizedHistory: [{ label: '2026-03-20', balance: 90 }],
        timeline: [{ label: '2026-03-22', forecast_balance: 100, actual_balance: null }],
        assetBalance: 1200,
        liabilityBalance: 450,
        netBalance: 750,
      },
    })

    expect(wrapper.text()).toContain('Month · Debt composition')
    expect(chartConstructor.mock.calls[0][1].data.datasets).toEqual([
      expect.objectContaining({ label: 'Assets', data: [1200, 1200] }),
      expect.objectContaining({ label: 'Liabilities', data: [450, 450] }),
      expect.objectContaining({ label: 'Net balance', data: [750, 750] }),
    ])
beforeAll(() => {
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
    canvas: document.createElement('canvas'),
  }))
})

const baseProps = {
  viewType: 'Month',
  graphMode: 'combined',
  realizedHistory: [{ date: '2024-01-01', label: 'H1', balance: 90 }],
  timeline: [{ date: '2024-01-02', label: 'F1', forecast_balance: 100, actual_balance: null }],
  series: {
    realized_income: {
      id: 'realized_income',
      label: 'Realized income used for auto-calculation',
      points: [{ date: '2024-01-01', label: '2024-01-01', value: 20 }],
    },
    manual_adjustments: {
      id: 'manual_adjustments',
      label: 'Manual adjustments',
      points: [{ date: '2024-01-02', label: '2024-01-02', value: 5 }],
    },
    spending: {
      id: 'spending',
      label: 'Spending',
      points: [{ date: '2024-01-02', label: '2024-01-02', value: -12 }],
    },
    debt_totals: {
      id: 'debt_totals',
      label: 'Debt totals',
      points: [{ date: '2024-01-02', label: '2024-01-02', value: 40 }],
    },
  },
  computeMeta: {
    lookbackDays: 90,
    movingAverageWindow: 30,
    normalize: false,
    includesAutoDetectedAdjustments: true,
    autoDetectedAdjustmentCount: 2,
  },
}

describe('ForecastChart', () => {
  it('renders the chart canvas and methodology help text', () => {
    const wrapper = mount(ForecastChart, {
      props: baseProps,
    })

    expect(wrapper.find('canvas').exists()).toBe(true)
    expect(wrapper.text()).toContain('How this forecast is calculated')
    expect(wrapper.text()).toContain('latest 90 days of realized history')
    expect(wrapper.text()).toContain('30-day moving average')
    expect(wrapper.text()).toContain('Normalization is off')
    expect(wrapper.text()).toContain('Auto-detected adjustments are included (2 detected)')
    const chartConfig = (Chart as unknown as ReturnType<typeof vi.fn>).mock.calls[0][1]
    expect(chartConfig.data.datasets.map((dataset: { label: string }) => dataset.label)).toEqual(
      expect.arrayContaining([
        'Historical balance',
        'Forecast balance',
        'Realized income used for auto-calculation',
        'Manual adjustments',
        'Spending',
        'Debt totals',
      ]),
    )
  })

  it('updates methodology help text when compute controls change', async () => {
    const wrapper = mount(ForecastChart, {
      props: baseProps,
    })

    await wrapper.setProps({
      graphMode: 'forecast',
      computeMeta: {
        lookbackDays: 60,
        movingAverageWindow: 7,
        normalize: true,
        includesAutoDetectedAdjustments: false,
        autoDetectedAdjustmentCount: 0,
      },
    })

    expect(wrapper.text()).toContain('latest 60 days of realized history')
    expect(wrapper.text()).toContain('7-day moving average')
    expect(wrapper.text()).toContain('renders in forecast mode')
    expect(wrapper.text()).toContain('Normalization is on')
    expect(wrapper.text()).toContain('Auto-detected adjustments are not included')
  })

  it('emits a view update when toggled', async () => {
    const wrapper = mount(ForecastChart, {
      props: baseProps,
    })

    await wrapper.get('.toggle-button').trigger('click')

    expect(wrapper.emitted('update:viewType')).toEqual([['Year']])
  })
})
