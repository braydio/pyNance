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

describe('DailyNetChart density config', () => {
  beforeEach(() => {
    chartCtor.mockClear()
    fetchDailyNet.mockReset()
    fetchDailyNet.mockResolvedValue({
      status: 'success',
      data: [
        {
          date: '2024-01-01',
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

  it('uses compact bars, fewer ticks, and month labels for dense ranges', async () => {
    mount(DailyNetChart, {
      props: {
        startDate: '2024-01-01',
        endDate: '2024-05-31',
      },
    })

    await flushRender()

    const config = chartCtor.mock.calls.at(-1)[0]
    const expenseDataset = config.data.datasets.find((d) => d.label === 'Expenses')

    expect(config.data.labels).toHaveLength(152)
    expect(expenseDataset.barThickness).toBe(5)
    expect(expenseDataset.maxBarThickness).toBe(8)
    expect(expenseDataset.categoryPercentage).toBe(0.92)
    expect(expenseDataset.barPercentage).toBe(0.8)
    expect(config.options.scales.x.ticks.maxTicksLimit).toBe(6)
    expect(config.options.scales.x.ticks.callback(null, 0)).toBe('Jan')
  })

  it('uses standard day labels and medium sizing for medium ranges', async () => {
    mount(DailyNetChart, {
      props: {
        startDate: '2024-01-01',
        endDate: '2024-03-01',
      },
    })

    await flushRender()

    const config = chartCtor.mock.calls.at(-1)[0]
    const incomeDataset = config.data.datasets.find((d) => d.label === 'Income')

    expect(config.data.labels).toHaveLength(61)
    expect(incomeDataset.barThickness).toBe(10)
    expect(incomeDataset.maxBarThickness).toBe(14)
    expect(config.options.scales.x.ticks.maxTicksLimit).toBe(8)
    expect(config.options.scales.x.ticks.callback(null, 0)).toBe('Jan 1')
  })
})
