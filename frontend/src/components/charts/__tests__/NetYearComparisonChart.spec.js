// @vitest-environment jsdom

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import NetYearComparisonChart from '../NetYearComparisonChart.vue'

const chartCalls = []

const apiMocks = vi.hoisted(() => {
  const currentYear = new Date().getFullYear()
  const previousYear = currentYear - 1

  return {
    fetchNetAssets: vi.fn().mockResolvedValue({
      status: 'success',
      data: [
        {
          date: `${currentYear}-01-01`,
          assets: 1500,
          liabilities: 350,
          net_assets: 1150,
        },
        {
          date: `${previousYear}-01-01`,
          assets: 1200,
          liabilities: 400,
          net_assets: 800,
        },
      ],
    }),
  }
})

vi.mock('chart.js/auto', () => {
  const Chart = vi.fn().mockImplementation((_ctx, config) => {
    chartCalls.push(config)
    return { destroy: vi.fn() }
  })
  return { Chart, default: Chart }
})

vi.mock('@/services/api', () => ({
  default: {
    fetchNetAssets: apiMocks.fetchNetAssets,
  },
}))

describe('NetYearComparisonChart', () => {
  beforeEach(() => {
    chartCalls.length = 0
    apiMocks.fetchNetAssets.mockClear()
    vi.spyOn(window.HTMLCanvasElement.prototype, 'getContext').mockReturnValue({})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('normalises backend payload so net worth series renders', async () => {
    const wrapper = mount(NetYearComparisonChart)
    await flushPromises()

    const netWorthButton = wrapper.findAll('button').find((button) => button.text() === 'Net Worth')
    expect(netWorthButton).toBeTruthy()

    await netWorthButton.trigger('click')
    await flushPromises()

    const config = chartCalls.at(-1)
    expect(config.data.datasets[0].label).toContain('Net Worth')

    const flattened = config.data.datasets
      .flatMap((dataset) => dataset.data)
      .filter((value) => typeof value === 'number')

    expect(flattened).toEqual(expect.arrayContaining([800, 1150]))
  })
})
