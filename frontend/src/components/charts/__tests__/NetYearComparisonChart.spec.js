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

describe('NetYearComparisonChart states', () => {
  it('exposes pressed state on the type toggles and a non-submitting button', async () => {
    const wrapper = mount(NetYearComparisonChart)
    await flushPromises()
    const buttons = wrapper.findAll('.toggle-group button')
    expect(buttons.map((b) => b.attributes('aria-pressed'))).toEqual(['true', 'false', 'false'])
    expect(buttons[0].attributes('type')).toBe('button')
    await buttons[1].trigger('click')
    expect(buttons[1].attributes('aria-pressed')).toBe('true')
  })

  it('shows an empty state when there is no history and an error with retry on failure', async () => {
    apiMocks.fetchNetAssets.mockResolvedValueOnce({ status: 'success', data: [] })
    const empty = mount(NetYearComparisonChart)
    await flushPromises()
    expect(empty.get('[data-testid="year-chart-empty"]').text()).toContain('No balance history')

    apiMocks.fetchNetAssets.mockRejectedValueOnce(new Error('down'))
    const failed = mount(NetYearComparisonChart)
    await flushPromises()
    expect(failed.get('[data-testid="year-chart-error"]').text()).toContain('Unable to load')
    await failed.get('[data-testid="year-chart-error"] button').trigger('click')
    await flushPromises()
    expect(failed.find('[data-testid="year-chart-error"]').exists()).toBe(false)
  })
})
