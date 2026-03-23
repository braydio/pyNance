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
  })
})
