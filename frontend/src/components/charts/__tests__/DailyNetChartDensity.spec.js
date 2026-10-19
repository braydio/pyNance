// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import DailyNetChart from '../DailyNetChart.vue'
import { fetchDailyNet } from '@/api/charts'

const chartCtor = vi.fn()

vi.mock('chart.js', () => {
  const Tooltip = { positioners: {} }
  const Chart = vi.fn().mockImplementation((_ctx, config) => {
    chartCtor(config)
    return {
      stop: vi.fn(),
      destroy: vi.fn(),
      data: config.data,
      scales: {},
      getElementsAtEventForMode: vi.fn().mockReturnValue([]),
      getDatasetMeta: vi.fn().mockReturnValue({ data: [] }),
    }
  })
  Chart.register = vi.fn()
  Chart.Tooltip = Tooltip

  return {
    Chart,
    Tooltip,
    Legend: {},
    LineElement: {},
    BarElement: {},
    CategoryScale: {},
    LinearScale: {},
    PointElement: {},
  }
})

vi.mock('@/api/charts', () => ({
  fetchDailyNet: vi.fn(),
}))

async function flushRender() {
  await Promise.resolve()
  await nextTick()
  await nextTick()
}

describe('DailyNetChart bar density by bucket count', () => {
  beforeEach(() => {
    chartCtor.mockClear()
    fetchDailyNet.mockReset()
    fetchDailyNet.mockResolvedValue({
      status: 'success',
      data: [
        {
          date: '2024-02-01',
          income: { parsedValue: 120 },
          expenses: { parsedValue: -40 },
          net: { parsedValue: 80 },
          transaction_count: 2,
        },
      ],
    })

    Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
      value: () => ({ canvas: {} }),
      writable: true,
    })
  })

  async function render(props) {
    mount(DailyNetChart, { props })
    await flushRender()
    return chartCtor.mock.calls.at(-1)[0]
  }

  it('draws a year-to-date range as monthly bars rather than one bar per day', async () => {
    const config = await render({ startDate: '2024-01-01', endDate: '2024-05-31', timeframe: 'ytd' })
    const expenses = config.data.datasets.find((d) => d.label === 'Expenses')

    expect(config.data.labels).toHaveLength(5)
    expect(expenses.maxBarThickness).toBe(64)
    expect(expenses.barThickness).toBeUndefined()
    expect(config.options.scales.x.ticks.callback(null, 0)).toBe('Jan')
    expect(config.options.scales.x.ticks.callback(null, 4)).toBe('May')
  })

  it('keeps daily ranges at one bar per day with narrower bars and day labels', async () => {
    const config = await render({ startDate: '2024-02-01', endDate: '2024-03-01', timeframe: 'custom' })
    const income = config.data.datasets.find((d) => d.label === 'Income')

    expect(config.data.labels).toHaveLength(30)
    expect(income.maxBarThickness).toBe(26)
    expect(config.options.scales.x.ticks.maxTicksLimit).toBe(10)
    expect(config.options.scales.x.ticks.callback(null, 0)).toBe('Feb 1')
  })

  it('formats the value axis as compact currency', async () => {
    const config = await render({ startDate: '2024-02-01', endDate: '2024-02-10', timeframe: 'custom' })
    const { callback } = config.options.scales.y.ticks
    expect(callback(1200)).toBe('$1.2k')
    expect(callback(-2400)).toBe('-$2.4k')
  })
})
