// @vitest-environment jsdom
/**
 * Component tests for DailyNetChart date padding, moving averages,
 * and comparison overlays.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import DailyNetChart from '../DailyNetChart.vue'
import { fetchDailyNet } from '@/api/charts'

const chartMock = vi.fn()

vi.mock('chart.js', async () => {
  const actual = await vi.importActual('chart.js')
  const ChartMock = vi.fn().mockImplementation((_ctx, config) => {
    chartMock(config)
    return {
      destroy: vi.fn(),
      stop: vi.fn(),
      data: config.data,
      getElementsAtEventForMode: vi.fn().mockReturnValue([]),
      getDatasetMeta: vi.fn().mockReturnValue({ data: [] }),
    }
  })
  ChartMock.register = vi.fn()

  return {
    ...actual,
    Chart: ChartMock,
  }
})

vi.mock('@/api/charts', () => ({
  fetchDailyNet: vi.fn(),
}))

/**
 * Format a Date object as YYYY-MM-DD.
 */
function formatDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Flush Vue + promise queues.
 */
async function flushRender() {
  await Promise.resolve()
  await nextTick()
}

describe('DailyNetChart.vue', () => {
  beforeEach(() => {
    chartMock.mockClear()
    fetchDailyNet.mockReset()

    fetchDailyNet.mockResolvedValue({
      status: 'success',
      data: [
        {
          date: '2024-06-02',
          income: { parsedValue: 100 },
          expenses: { parsedValue: -40 },
          net: { parsedValue: 60 },
          transaction_count: 2,
        },
        {
          date: '2024-06-15',
          income: { parsedValue: 200 },
          expenses: { parsedValue: -80 },
          net: { parsedValue: 120 },
          transaction_count: 3,
        },
      ],
    })

    if (typeof HTMLCanvasElement !== 'undefined') {
      Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
        value: () => ({}),
        writable: true,
      })
    }
  })

  it('pads chart labels and data for the full selected month', async () => {
    const wrapper = mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
      },
    })

    await flushRender()
    await flushRender()

    const lastConfig = chartMock.mock.calls.at(-1)[0]
    const labels = lastConfig.data.labels

    expect(labels).toHaveLength(30)
    expect(labels[0]).toBe('2024-06-01')
    expect(labels[29]).toBe('2024-06-30')

    const income = lastConfig.data.datasets.find((d) => d.label === 'Income')
    const expenses = lastConfig.data.datasets.find((d) => d.label === 'Expenses')

    expect(income.data).toHaveLength(30)
    expect(expenses.data).toHaveLength(30)

    expect(income.data[0]).toBe(0)
    expect(expenses.data[0]).toBe(0)

    const juneSecondIndex = labels.indexOf('2024-06-02')
    expect(income.data[juneSecondIndex]).toBe(100)
  })

  it('keeps labels aligned to the selected date range', async () => {
    const start = new Date('2024-02-10T00:00:00')
    const end = new Date(start.getFullYear(), 1, 29)

    mount(DailyNetChart, {
      props: {
        startDate: formatDateKey(start),
        endDate: formatDateKey(end),
        zoomedOut: false,
      },
    })

    await flushRender()
    await flushRender()

    const lastConfig = chartMock.mock.calls.at(-1)[0]
    const labels = lastConfig.data.labels

    expect(labels[0]).toBe(formatDateKey(start))
    expect(labels.at(-1)).toBe(formatDateKey(end))
  })

  it('pads sparse ranges and uses zeros in moving averages', async () => {
    fetchDailyNet.mockResolvedValueOnce({
      status: 'success',
      data: [
        {
          date: '2024-03-01',
          income: { parsedValue: 70 },
          expenses: { parsedValue: 0 },
          net: { parsedValue: 70 },
          transaction_count: 1,
        },
        {
          date: '2024-03-10',
          income: { parsedValue: 70 },
          expenses: { parsedValue: 0 },
          net: { parsedValue: 70 },
          transaction_count: 1,
        },
      ],
    })

    mount(DailyNetChart, {
      props: {
        startDate: '2024-03-01',
        endDate: '2024-03-10',
        zoomedOut: false,
        show7Day: true,
      },
    })

    await flushRender()
    await flushRender()

    const lastConfig = chartMock.mock.calls.at(-1)[0]
    const labels = lastConfig.data.labels

    expect(labels).toHaveLength(10)
    expect(labels[0]).toBe('2024-03-01')
    expect(labels.at(-1)).toBe('2024-03-10')

    const income = lastConfig.data.datasets.find((d) => d.label === 'Income')
    const ma7 = lastConfig.data.datasets.find((d) => d.label === '7-Day Avg')

    expect(income.data[1]).toBe(0)
    expect(ma7.data.at(-1)).toBeCloseTo(10, 5)
  })

  it('aligns prior month overlay values to day-of-month labels', async () => {
    fetchDailyNet
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-06-02',
            income: { parsedValue: 100 },
            expenses: { parsedValue: -40 },
            net: { parsedValue: 60 },
          },
          {
            date: '2024-06-15',
            income: { parsedValue: 200 },
            expenses: { parsedValue: -80 },
            net: { parsedValue: 120 },
          },
        ],
      })
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-05-02',
            net: { parsedValue: 55 },
          },
          {
            date: '2024-05-15',
            net: { parsedValue: 120 },
          },
        ],
      })

    const wrapper = mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
        showComparisonOverlay: true,
        timeframe: 'mtd',
      },
    })

    await flushRender()
    await flushRender()

    const lastConfig = chartMock.mock.calls.at(-1)[0]
    const labels = lastConfig.data.labels
    const comparison = lastConfig.data.datasets.find((d) => d.label === 'This Day Last Month')

    expect(comparison).toBeTruthy()

    expect(comparison.data[labels.indexOf('2024-06-02')]).toBe(55)
    expect(comparison.data[labels.indexOf('2024-06-15')]).toBe(120)
  })

  it('removes comparison dataset when overlay is disabled', async () => {
    fetchDailyNet
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-06-02',
            income: { parsedValue: 100 },
            expenses: { parsedValue: -40 },
            net: { parsedValue: 60 },
            transaction_count: 2,
          },
        ],
      })
      .mockResolvedValueOnce({ status: 'success', data: [] })

    const wrapper = mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
        showComparisonOverlay: true,
        timeframe: 'mtd',
      },
    })

    await flushRender()
    await flushRender()

    let lastConfig = chartMock.mock.calls.at(-1)[0]
    expect(lastConfig.data.datasets.some((d) => d.label === 'This Day Last Month')).toBe(true)

    await wrapper.setProps({ showComparisonOverlay: false })
    await flushRender()
    await flushRender()

    lastConfig = chartMock.mock.calls.at(-1)[0]
    expect(lastConfig.data.datasets.some((d) => d.label === 'This Day Last Month')).toBe(false)
  })

  it('disables chartjs tooltip rendering', async () => {
    mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
      },
    })

    await flushRender()
    await flushRender()

    const lastConfig = chartMock.mock.calls.at(-1)[0]

    expect(lastConfig.options.plugins.tooltip.enabled).toBe(false)
  })

  it('renders persistent details with comparison metrics for the active day', async () => {
    fetchDailyNet
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-06-02',
            income: { parsedValue: 100 },
            expenses: { parsedValue: -40 },
            net: { parsedValue: 60 },
            transaction_count: 2,
          },
        ],
      })
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-05-02',
            net: { parsedValue: 55 },
          },
        ],
      })

    const wrapper = mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
        showComparisonOverlay: true,
        timeframe: 'mtd',
      },
    })

    await flushRender()
    await flushRender()

    const details = wrapper.find('.daily-net-chart__details')
    expect(details.exists()).toBe(true)
    expect(details.text()).toContain('Jun 02, 2024')
    expect(details.text()).toContain('Net: $60.00')
    expect(details.text()).toContain('Income')
    expect(details.text()).toContain('$100.00')
    expect(details.text()).toContain('Expenses')
    expect(details.text()).toContain('($40.00)')
    expect(details.text()).toContain('Transactions')
    expect(details.text()).toContain('2')
    expect(details.text()).toContain('This Day Last Month: $55.00')
    expect(details.text()).toContain('vs prior: +$5.00 (+9.1%)')
  })

  it('omits noisy percent text when comparison value is zero in details panel', async () => {
    fetchDailyNet
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-06-02',
            income: null,
            expenses: null,
            net: { parsedValue: 60 },
            transaction_count: null,
          },
        ],
      })
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-05-02',
            net: { parsedValue: 0 },
          },
        ],
      })

    const wrapper = mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
        showComparisonOverlay: true,
        timeframe: 'mtd',
      },
    })

    await flushRender()
    await flushRender()

    const details = wrapper.find('.daily-net-chart__details')
    expect(details.text()).toContain('This Day Last Month: $0.00')
    expect(details.text()).toContain('vs prior: +$60.00')
    expect(details.text()).not.toContain('%')
  })

  it('renders a legend row for active overlays in dataset order', async () => {
    const wrapper = mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
        showAvgIncome: true,
        show30Day: true,
        show7Day: true,
      },
    })

    await flushRender()
    await flushRender()

    const legendLabels = wrapper
      .findAll('.daily-net-chart__legend-label')
      .map((node) => node.text())

    expect(legendLabels).toEqual(['Avg Income', '30-Day Avg', '7-Day Avg'])
  })

  it('renders an empty state and skips chart creation when range has no transactions', async () => {
    fetchDailyNet.mockResolvedValueOnce({ status: 'success', data: [] })

    const wrapper = mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
      },
    })

    await flushRender()
    await flushRender()

    expect(wrapper.text()).toContain('No transactions found for the selected date range.')
    expect(wrapper.find('canvas').exists()).toBe(false)
    expect(chartMock).not.toHaveBeenCalled()
  })

  it('renders an error banner with retry action when data fetch fails', async () => {
    fetchDailyNet.mockRejectedValueOnce(new Error('request failed')).mockResolvedValueOnce({
      status: 'success',
      data: [
        {
          date: '2024-06-02',
          income: { parsedValue: 100 },
          expenses: { parsedValue: -40 },
          net: { parsedValue: 60 },
          transaction_count: 2,
        },
      ],
    })

    const wrapper = mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
      },
    })

    await flushRender()
    await flushRender()

    expect(wrapper.text()).toContain('Unable to load daily net data right now. Please try again.')
    expect(wrapper.find('button.daily-net-chart__retry').exists()).toBe(true)
    expect(chartMock).not.toHaveBeenCalled()

    await wrapper.find('button.daily-net-chart__retry').trigger('click')
    await flushRender()
    await flushRender()

    expect(fetchDailyNet).toHaveBeenCalledTimes(2)
    expect(chartMock.mock.calls.length).toBeGreaterThanOrEqual(1)
    expect(wrapper.text()).not.toContain(
      'Unable to load daily net data right now. Please try again.',
    )
  })
})
