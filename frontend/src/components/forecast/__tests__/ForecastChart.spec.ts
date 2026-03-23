// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
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

beforeAll(() => {
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
    canvas: document.createElement('canvas'),
  }))
})

const baseProps = {
  viewType: 'Month',
  graphMode: 'combined',
  selectedAspect: 'balances',
  realizedHistory: [{ date: '2024-01-01', label: 'H1', balance: 90 }],
  timeline: [{ date: '2024-01-02', label: 'F1', forecast_balance: 100, actual_balance: null }],
  series: {
    realized_income: {
      id: 'realized_income',
      label: 'Realized income used for auto-calculation',
      points: [{ date: '2024-01-01', label: '2024-01-01', value: 20, metadata: {} }],
    },
    manual_adjustments: {
      id: 'manual_adjustments',
      label: 'Manual adjustments',
      points: [{ date: '2024-01-02', label: '2024-01-02', value: 5, metadata: {} }],
    },
    spending: {
      id: 'spending',
      label: 'Spending',
      points: [{ date: '2024-01-02', label: '2024-01-02', value: -12, metadata: {} }],
    },
    debt_totals: {
      id: 'debt_totals',
      label: 'Total debt',
      points: [{ date: '2024-01-02', label: '2024-01-02', value: 40, metadata: {} }],
    },
    debt_interest: {
      id: 'debt_interest',
      label: 'Debt interest accrual',
      points: [{ date: '2024-01-02', label: '2024-01-02', value: 3, metadata: {} }],
    },
    debt_new_spending: {
      id: 'debt_new_spending',
      label: 'Debt new spending',
      points: [{ date: '2024-01-02', label: '2024-01-02', value: 7, metadata: {} }],
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

  it('updates methodology help text when compute controls change', async () => {
    const wrapper = mount(ForecastChart, {
      props: baseProps,
    })

    expect(wrapper.text()).toContain('latest 90 days of realized history')
    expect(wrapper.text()).toContain('30-day moving average')
    expect(wrapper.text()).toContain('Normalization is off')
    expect(wrapper.text()).toContain('Auto-detected adjustments are included (2 detected)')

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

  it('renders realized income from the typed backend series without balance overlays', async () => {
    mount(ForecastChart, {
      props: {
        ...baseProps,
        graphMode: 'historical',
        selectedAspect: 'realized_income',
      },
    })

    expect(chartConstructor.mock.calls[0][1].data.datasets).toEqual([
      expect.objectContaining({
        label: 'Realized income used for auto-calculation',
        data: [20, null],
      }),
    ])
  })

  it('renders debt total alongside debt component series', () => {
    const wrapper = mount(ForecastChart, {
      props: {
        ...baseProps,
        selectedAspect: 'debt',
      },
    })

    expect(wrapper.text()).toContain('Month · Debt composition')
    expect(chartConstructor.mock.calls[0][1].data.datasets).toEqual([
      expect.objectContaining({ label: 'Total debt', data: [null, 40] }),
      expect.objectContaining({ label: 'Debt interest accrual', data: [null, 3] }),
      expect.objectContaining({ label: 'Debt new spending', data: [null, 7] }),
    ])
  })

  it('emits a view update when toggled', async () => {
    const wrapper = mount(ForecastChart, {
      props: baseProps,
    })

    await wrapper.get('.toggle-button').trigger('click')

    expect(wrapper.emitted('update:viewType')).toEqual([['Year']])
  })

  it('destroys the chart instance when the component unmounts', () => {
    const wrapper = mount(ForecastChart, {
      props: baseProps,
    })

    wrapper.unmount()

    expect(chartDestroySpy).toHaveBeenCalled()
    expect(Chart).toBeDefined()
  })
})
