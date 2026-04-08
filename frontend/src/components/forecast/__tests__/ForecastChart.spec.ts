// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ForecastChart from '../ForecastChart.vue'

const { chartConstructor, chartDestroySpy } = vi.hoisted(() => {
  const destroySpy = vi.fn()
  const constructor = vi.fn().mockImplementation(() => ({ destroy: destroySpy }))
  return {
    chartConstructor: constructor,
    chartDestroySpy: destroySpy,
  }
})

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

const baseProps = {
  viewType: 'Month' as const,
  graphMode: 'combined' as const,
  selectedAspect: 'balances' as const,
  realizedHistory: [{ date: '2024-01-01', label: '2024-01-01', balance: 90 }],
  timeline: [
    { date: '2024-01-02', label: '2024-01-02', forecast_balance: 100, actual_balance: null },
  ],
  series: {
    realized_income: {
      id: 'realized_income' as const,
      label: 'Realized income used for auto-calculation',
      points: [{ date: '2024-01-01', label: '2024-01-01', value: 20 }],
    },
    manual_adjustments: {
      id: 'manual_adjustments' as const,
      label: 'Manual adjustments',
      points: [{ date: '2024-01-02', label: '2024-01-02', value: 5 }],
    },
    spending: {
      id: 'spending' as const,
      label: 'Spending',
      points: [{ date: '2024-01-02', label: '2024-01-02', value: -12 }],
    },
    debt_totals: {
      id: 'debt_totals' as const,
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
  beforeEach(() => {
    chartConstructor.mockClear()
    chartDestroySpy.mockClear()
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      canvas: document.createElement('canvas'),
    }))
  })

  it('renders balance history and forecast datasets in combined mode', () => {
    const wrapper = mount(ForecastChart, {
      props: baseProps,
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
        label: 'Forecast balance',
        data: [null, 100],
      }),
    ])
  })

  it('respects graph mode for the balance overlay', () => {
    mount(ForecastChart, {
      props: {
        ...baseProps,
        graphMode: 'historical',
      },
    })

    expect(chartConstructor.mock.calls[0][1].data.datasets).toEqual([
      expect.objectContaining({
        label: 'Historical balance',
        data: [90, null],
      }),
    ])
  })

  it('renders the selected typed series without reconstructing from cashflows', () => {
    const wrapper = mount(ForecastChart, {
      props: {
        ...baseProps,
        selectedAspect: 'realized_income',
        graphMode: 'historical',
      },
    })

    expect(wrapper.text()).toContain('Month · Realized income')
    expect(chartConstructor.mock.calls[0][1].data.datasets).toEqual([
      expect.objectContaining({
        label: 'Realized income used for auto-calculation',
        data: [20, null],
      }),
    ])
  })

  it('renders debt totals from the backend series', () => {
    const wrapper = mount(ForecastChart, {
      props: {
        ...baseProps,
        selectedAspect: 'debt',
      },
    })

    expect(wrapper.text()).toContain('Month · Debt composition')
    expect(chartConstructor.mock.calls[0][1].data.datasets).toEqual([
      expect.objectContaining({
        label: 'Debt totals',
        data: [null, 40],
        borderDash: [4, 4],
      }),
    ])
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
