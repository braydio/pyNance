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
const clickPoints = vi.hoisted(() => ({ value: [] }))

vi.mock('chart.js', async () => {
  const actual = await vi.importActual('chart.js')
  const ChartMock = vi.fn().mockImplementation((_ctx, config) => {
    chartMock(config)
    return {
      destroy: vi.fn(),
      stop: vi.fn(),
      data: config.data,
      getElementsAtEventForMode: vi.fn(() => clickPoints.value),
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
    clickPoints.value = []
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
    fetchDailyNet.mockResolvedValueOnce({
      status: 'success',
      data: [{ date: '2024-02-12', income: { parsedValue: 5 }, expenses: { parsedValue: 0 }, net: { parsedValue: 5 } }],
    })
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

    mount(DailyNetChart, {
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

  it('compares a custom range with the preceding window of the same inclusive length', async () => {
    fetchDailyNet
      .mockResolvedValueOnce({
        status: 'success',
        data: [{ date: '2025-03-02', net: { parsedValue: 10 } }],
      })
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          { date: '2025-02-20', net: { parsedValue: 7 } },
          { date: '2025-03-01', net: { parsedValue: 9 } },
        ],
      })

    mount(DailyNetChart, {
      props: {
        startDate: '2025-03-02',
        endDate: '2025-03-11',
        zoomedOut: false,
        showComparisonOverlay: true,
        timeframe: 'custom',
      },
    })

    await flushRender()
    await flushRender()

    // 10 inclusive days => prior window is 2025-02-20 .. 2025-03-01 (not 30 days, not prior MTD).
    expect(fetchDailyNet).toHaveBeenLastCalledWith({
      start_date: '2025-02-20',
      end_date: '2025-03-01',
    })
    const lastConfig = chartMock.mock.calls.at(-1)[0]
    const labels = lastConfig.data.labels
    const comparison = lastConfig.data.datasets.find((d) => d.label === 'Previous period')
    expect(comparison).toBeTruthy()
    expect(comparison.data[labels.indexOf('2025-03-02')]).toBe(7)
    expect(comparison.data[labels.indexOf('2025-03-11')]).toBe(9)
  })

  it('keeps a DST-spanning custom comparison aligned to whole days', async () => {
    fetchDailyNet.mockResolvedValue({ status: 'success', data: [] })

    mount(DailyNetChart, {
      props: {
        startDate: '2025-03-09',
        endDate: '2025-03-12',
        zoomedOut: false,
        showComparisonOverlay: true,
        timeframe: 'custom',
      },
    })
    await flushRender()
    await flushRender()

    expect(fetchDailyNet).toHaveBeenLastCalledWith({
      start_date: '2025-03-05',
      end_date: '2025-03-08',
    })
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

  it('renders persistent details panel content for selected indices with comparison deltas', async () => {
    fetchDailyNet
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-06-01',
            income: { parsedValue: 80 },
            expenses: { parsedValue: -20 },
            net: { parsedValue: 60 },
            transaction_count: 1,
          },
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
            date: '2024-05-01',
            net: { parsedValue: 90 },
          },
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

    const lastConfig = chartMock.mock.calls.at(-1)[0]
    const details = wrapper.find('.daily-net-chart__details')
    expect(details.exists()).toBe(true)
    expect(details.text()).toContain('Jun 1, 2024')
    expect(details.text()).toContain('Net: $60.00')
    expect(details.text()).toContain('Income')
    expect(details.text()).toContain('$80.00')
    expect(details.text()).toContain('Expenses')
    expect(details.text()).toContain('($20.00)')
    expect(details.text()).toContain('Transactions')
    expect(details.text()).toContain('1')
    expect(details.text()).toContain('This Day Last Month: $90.00')
    expect(details.text()).toContain('vs prior: ($30.00) (-33.3%)')

    lastConfig.options.onHover({}, [{ index: 1 }])
    await flushRender()

    expect(details.text()).toContain('Jun 2, 2024')
    expect(details.text()).toContain('Net: $60.00')
    expect(details.text()).toContain('Income')
    expect(details.text()).toContain('$100.00')
    expect(details.text()).toContain('Expenses')
    expect(details.text()).toContain('($40.00)')
    expect(details.text()).toContain('Transactions')
    expect(details.text()).toContain('2')
    expect(details.text()).toContain('This Day Last Month: $55.00')
    expect(details.text()).toContain('vs prior: +$5.00 (+9.1%)')

    lastConfig.options.onHover({}, [{ index: 0 }])
    await flushRender()

    expect(details.text()).toContain('Jun 1, 2024')
    expect(details.text()).toContain('Net: $60.00')
    expect(details.text()).toContain('Income')
    expect(details.text()).toContain('$80.00')
    expect(details.text()).toContain('Expenses')
    expect(details.text()).toContain('($20.00)')
    expect(details.text()).toContain('Transactions')
    expect(details.text()).toContain('1')
    expect(details.text()).toContain('This Day Last Month: $90.00')
    expect(details.text()).toContain('vs prior: ($30.00) (-33.3%)')
  })

  it('updates details on hover and keeps last selection when hover exits', async () => {
    fetchDailyNet.mockResolvedValueOnce({
      status: 'success',
      data: [
        {
          date: '2024-06-01',
          income: { parsedValue: 10 },
          expenses: { parsedValue: -2 },
          net: { parsedValue: 8 },
          transaction_count: 1,
        },
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
        endDate: '2024-06-02',
        zoomedOut: false,
      },
    })

    await flushRender()
    await flushRender()

    const lastConfig = chartMock.mock.calls.at(-1)[0]
    expect(wrapper.find('.daily-net-chart__details').text()).toContain('Jun 2, 2024')

    lastConfig.options.onHover({}, [{ index: 0 }])
    await flushRender()
    expect(wrapper.find('.daily-net-chart__details').text()).toContain('Jun 1, 2024')

    lastConfig.options.onHover({}, [])
    await flushRender()
    expect(wrapper.find('.daily-net-chart__details').text()).toContain('Jun 1, 2024')
  })

  it('keeps selected index through overlay rerenders and recomputes comparison details', async () => {
    fetchDailyNet
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-06-01',
            income: { parsedValue: 100 },
            expenses: { parsedValue: -10 },
            net: { parsedValue: 90 },
            transaction_count: 1,
          },
          {
            date: '2024-06-02',
            income: { parsedValue: 120 },
            expenses: { parsedValue: -20 },
            net: { parsedValue: 100 },
            transaction_count: 2,
          },
        ],
      })
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          { date: '2024-05-01', net: { parsedValue: 80 } },
          { date: '2024-05-02', net: { parsedValue: 70 } },
        ],
      })
      .mockResolvedValue({
        status: 'success',
        data: [
          { date: '2024-05-01', net: { parsedValue: 80 } },
          { date: '2024-05-02', net: { parsedValue: 70 } },
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
    await flushRender()

    let lastConfig = chartMock.mock.calls.at(-1)[0]
    lastConfig.options.onHover({}, [{ index: 0 }])
    await flushRender()
    expect(wrapper.find('.daily-net-chart__details').text()).toContain(
      'This Day Last Month: $80.00',
    )

    await wrapper.setProps({ showComparisonOverlay: false })
    await flushRender()
    await flushRender()

    expect(wrapper.find('.daily-net-chart__details').text()).toContain('Jun 1, 2024')
    expect(wrapper.find('.daily-net-chart__details').text()).not.toContain('This Day Last Month')

    await wrapper.setProps({ showComparisonOverlay: true })
    await flushRender()
    await flushRender()

    lastConfig = chartMock.mock.calls.at(-1)[0]
    lastConfig.options.onHover({}, [{ index: 0 }])
    await flushRender()
    expect(wrapper.find('.daily-net-chart__details').text()).toContain(
      'This Day Last Month: $80.00',
    )
  })

  it('defaults to latest non-empty day on first render and clamps selection after range changes', async () => {
    fetchDailyNet
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-06-30',
            income: { parsedValue: 10 },
            expenses: { parsedValue: 0 },
            net: { parsedValue: 10 },
            transaction_count: 1,
          },
        ],
      })
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-07-02',
            income: { parsedValue: 200 },
            expenses: { parsedValue: -50 },
            net: { parsedValue: 150 },
            transaction_count: 4,
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

    expect(wrapper.find('.daily-net-chart__details').text()).toContain('Jun 30, 2024')

    await wrapper.setProps({ startDate: '2024-07-01', endDate: '2024-07-02' })
    await flushRender()
    await flushRender()

    const detailsText = wrapper.find('.daily-net-chart__details').text()
    expect(detailsText).toContain('Jul 2, 2024')
    expect(detailsText).toContain('Net: $150.00')
    expect(detailsText).toContain('Transactions')
    expect(detailsText).toContain('4')
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
      .findAll('.daily-net-chart__legend--overlays .daily-net-chart__legend-label')
      .map((node) => node.text())

    expect(legendLabels).toEqual(['Avg Income', '30-Day Avg', '7-Day Avg'])
  })

  it('includes comparison overlay in the horizontal legend when enabled', async () => {
    fetchDailyNet
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-06-02',
            income: { parsedValue: 180 },
            expenses: { parsedValue: -80 },
            net: { parsedValue: 100 },
            transaction_count: 2,
          },
        ],
      })
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-05-02',
            net: { parsedValue: 70 },
          },
        ],
      })

    const wrapper = mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
        showComparisonOverlay: true,
        showAvgExpenses: true,
      },
    })

    await flushRender()
    await flushRender()

    const legendLabels = wrapper
      .findAll('.daily-net-chart__legend--overlays .daily-net-chart__legend-label')
      .map((node) => node.text())

    expect(legendLabels).toEqual(['Avg Expenses', 'This Day Last Month'])
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

    expect(wrapper.text()).toContain('No activity in this period')
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

const money = (value) => ({ source: String(value), parsedValue: value })
const dayRow = (date, income, expenses, refunds = 0, extra = {}) => ({
  date,
  income: money(income),
  expenses: money(expenses),
  refunds,
  net: money(Math.round((income + expenses + refunds) * 100) / 100),
  transaction_count: 1,
  ...extra,
})

function deferred() {
  let resolve
  const promise = new Promise((r) => {
    resolve = r
  })
  return { promise, resolve }
}

describe('DailyNetChart period buckets', () => {
  beforeEach(() => {
    chartMock.mockClear()
    clickPoints.value = []
    fetchDailyNet.mockReset()
  })

  const lastConfig = () => chartMock.mock.calls.at(-1)[0]
  async function settle() {
    await flushRender()
    await flushRender()
    await flushRender()
  }

  it('shows economic net with a separate refund segment in daily, weekly and monthly views', async () => {
    const rows = [
      dayRow('2026-10-05', 1000, -300, 25, {
        transfer_in: 200,
        debt_settlement: 131.64,
        unclassified_inflows: 100,
      }),
    ]
    for (const [timeframe, start, label] of [
      ['custom', '2026-10-01', 'daily'],
      ['3m', '2026-08-01', 'weekly'],
      ['ytd', '2026-01-01', 'monthly'],
    ]) {
      fetchDailyNet.mockResolvedValue({ status: 'success', data: rows })
      const wrapper = mount(DailyNetChart, {
        props: { startDate: start, endDate: '2026-10-19', timeframe },
      })
      await settle()
      const config = lastConfig()
      const at = (name) => config.data.datasets.find((d) => d.label === name).data
      const idx = at('Income').findIndex((v) => v !== 0)
      expect(at('Income')[idx]).toBe(1000)
      expect(at('Expenses')[idx]).toBe(-300)
      expect(at('Refunds')[idx]).toBe(25)
      const details = wrapper.get('.daily-net-chart__details').text()
      expect(details).toContain('Economic Net: $725.00')
      expect(details).not.toContain('$700.00')
      expect(wrapper.text()).toContain(`${label[0].toUpperCase()}${label.slice(1)} economic net table`)
      wrapper.unmount()
    }
  })

  it.each([
    ['7d', '2026-10-13', 7],
    ['rolling_30', '2026-09-20', 30],
    ['mtd', '2026-10-01', 19],
  ])('draws %s as one local day per bar', async (timeframe, start, count) => {
    fetchDailyNet.mockResolvedValue({ status: 'success', data: [dayRow('2026-10-15', 10, -2)] })
    mount(DailyNetChart, { props: { startDate: start, endDate: '2026-10-19', timeframe } })
    await settle()
    expect(lastConfig().data.labels).toHaveLength(count)
  })

  it('draws YTD as exactly ten month bars with a partial October and never daily bars', async () => {
    fetchDailyNet.mockResolvedValue({ status: 'success', data: [dayRow('2026-03-02', 10, -2)] })
    const wrapper = mount(DailyNetChart, {
      props: { startDate: '2026-01-01', endDate: '2026-10-19', timeframe: 'ytd' },
    })
    await settle()
    const config = lastConfig()
    expect(config.data.labels).toHaveLength(10)
    expect(config.data.labels[0]).toBe('2026-01-01')
    expect(config.data.labels[9]).toBe('2026-10-01')
    const last = wrapper.findAll('.daily-net-chart__table tbody tr').at(-1)
    expect(last.text()).toContain('Oct 2026 (Oct 1–19)')
  })

  it('accepts every dashboard preset as a timeframe', () => {
    const validator = DailyNetChart.props.timeframe.validator
    ;['7d', 'rolling_30', 'mtd', '3m', '6m', 'ytd', '1y', 'custom'].forEach((value) =>
      expect(validator(value)).toBe(true),
    )
    expect(validator('quarterly')).toBe(false)
  })

  it('emits daily source rows and totals incl. refunds for the selected period only', async () => {
    fetchDailyNet.mockResolvedValue({
      status: 'success',
      data: [dayRow('2026-09-25', 999, -1), dayRow('2026-10-05', 1000, -300, 25)],
    })
    const wrapper = mount(DailyNetChart, {
      props: { startDate: '2026-10-01', endDate: '2026-10-19', timeframe: 'ytd', show7Day: true },
    })
    await settle()
    expect(wrapper.emitted('summary-change').at(-1)[0]).toMatchObject({
      totalIncome: 1000,
      totalExpenses: -300,
      totalRefunds: 25,
      totalNet: 725,
    })
    const daily = wrapper.emitted('data-change').at(-1)[0]
    expect(daily).toHaveLength(19)
    expect(daily[0].date).toBe('2026-10-01')
  })

  it('emits zero summary and an empty series when the period has no activity', async () => {
    fetchDailyNet.mockResolvedValue({ status: 'success', data: [dayRow('2026-09-25', 50, -5)] })
    const wrapper = mount(DailyNetChart, {
      props: { startDate: '2026-10-01', endDate: '2026-10-19', show7Day: true },
    })
    await settle()
    expect(wrapper.text()).toContain('No activity in this period')
    expect(wrapper.emitted('summary-change').at(-1)[0]).toMatchObject({
      totalIncome: 0,
      totalExpenses: 0,
      totalRefunds: 0,
      totalNet: 0,
    })
    expect(wrapper.emitted('data-change').at(-1)[0]).toEqual([])
  })

  it('drills a monthly bar into its days, then restores YTD without touching global dates', async () => {
    fetchDailyNet.mockResolvedValue({
      status: 'success',
      data: [dayRow('2026-02-10', 100, -20), dayRow('2026-03-04', 40, -10)],
    })
    const wrapper = mount(DailyNetChart, {
      props: { startDate: '2026-01-01', endDate: '2026-10-19', timeframe: 'ytd' },
    })
    await settle()
    expect(fetchDailyNet).toHaveBeenCalledTimes(1)

    clickPoints.value = [{ index: 1 }]
    lastConfig().options.onClick({})
    await settle()

    expect(wrapper.emitted('bar-click')).toBeUndefined()
    expect(wrapper.get('.daily-net-chart__back').text()).toContain('Back to Monthly')
    expect(wrapper.get('.daily-net-chart__crumb').text()).toContain('Feb 2026')
    const config = lastConfig()
    expect(config.data.labels).toHaveLength(28)
    expect(config.data.labels[0]).toBe('2026-02-01')
    expect(config.data.labels.at(-1)).toBe('2026-02-28')
    expect(fetchDailyNet).toHaveBeenCalledTimes(1)
    // The parent still gets the whole YTD period, not the drilled month.
    expect(wrapper.emitted('data-change')).toHaveLength(1)

    clickPoints.value = [{ index: 9 }]
    lastConfig().options.onClick({})
    await settle()
    expect(wrapper.emitted('bar-click').at(-1)).toEqual(['2026-02-10'])

    await wrapper.get('.daily-net-chart__back').trigger('click')
    await settle()
    expect(wrapper.find('.daily-net-chart__back').exists()).toBe(false)
    expect(lastConfig().data.labels).toHaveLength(10)
    expect(wrapper.get('.daily-net-chart__details').text()).toContain('Feb 2026')
  })

  it('opens the day modal directly from a daily bar', async () => {
    fetchDailyNet.mockResolvedValue({ status: 'success', data: [dayRow('2026-10-15', 10, -2)] })
    const wrapper = mount(DailyNetChart, {
      props: { startDate: '2026-10-13', endDate: '2026-10-19', timeframe: '7d' },
    })
    await settle()
    clickPoints.value = [{ index: 2 }]
    lastConfig().options.onClick({})
    expect(wrapper.emitted('bar-click').at(-1)).toEqual(['2026-10-15'])
    expect(wrapper.find('.daily-net-chart__back').exists()).toBe(false)
  })

  it('resets the drilldown when the global period changes', async () => {
    fetchDailyNet.mockResolvedValue({ status: 'success', data: [dayRow('2026-02-10', 100, -20)] })
    const wrapper = mount(DailyNetChart, {
      props: { startDate: '2026-01-01', endDate: '2026-10-19', timeframe: 'ytd' },
    })
    await settle()
    clickPoints.value = [{ index: 1 }]
    lastConfig().options.onClick({})
    await settle()
    expect(wrapper.find('.daily-net-chart__back').exists()).toBe(true)

    await wrapper.setProps({ startDate: '2026-10-13', endDate: '2026-10-19', timeframe: '7d' })
    await settle()
    expect(wrapper.find('.daily-net-chart__back').exists()).toBe(false)
  })

  it('supports keyboard navigation, drilldown and escape without a pointer', async () => {
    fetchDailyNet.mockResolvedValue({
      status: 'success',
      data: [dayRow('2026-01-10', 100, -20), dayRow('2026-02-10', 60, -10)],
    })
    const wrapper = mount(DailyNetChart, {
      props: { startDate: '2026-01-01', endDate: '2026-03-31', timeframe: 'custom' },
    })
    await settle()
    // 90 days => weekly buckets; Home selects the first week.
    const wrap = wrapper.get('.daily-net-chart__canvas-wrap')
    expect(wrap.attributes('tabindex')).toBe('0')
    await wrap.trigger('keydown', { key: 'Home' })
    expect(wrapper.get('.daily-net-chart__details').text()).toContain('Jan 1–4, 2026')
    await wrap.trigger('keydown', { key: 'ArrowRight' })
    expect(wrapper.get('.daily-net-chart__details').text()).toContain('Jan 5–11, 2026')
    await wrap.trigger('keydown', { key: 'Enter' })
    await settle()
    expect(wrapper.get('.daily-net-chart__back').text()).toContain('Back to Weekly')
    expect(lastConfig().data.labels).toHaveLength(7)
    await wrap.trigger('keydown', { key: 'Escape' })
    await settle()
    expect(wrapper.find('.daily-net-chart__back').exists()).toBe(false)
  })

  it('exposes every bucket in an accessible table with text values', async () => {
    fetchDailyNet.mockResolvedValue({ status: 'success', data: [dayRow('2026-03-02', 100, -20, 5)] })
    const wrapper = mount(DailyNetChart, {
      props: { startDate: '2026-01-01', endDate: '2026-03-31', timeframe: 'ytd' },
    })
    await settle()
    const rows = wrapper.findAll('.daily-net-chart__table tbody tr')
    expect(rows).toHaveLength(3)
    expect(rows[2].text()).toContain('Mar 2026')
    expect(rows[2].text()).toContain('$100.00')
    expect(rows[2].text()).toContain('$5.00')
    expect(rows[2].text()).toContain('$85.00')
    await rows[2].get('button').trigger('click')
    await settle()
    expect(wrapper.get('.daily-net-chart__crumb').text()).toContain('Mar 2026')
  })

  it('always shows a legend for income, expenses, refunds when present, and the net dash', async () => {
    fetchDailyNet.mockResolvedValue({ status: 'success', data: [dayRow('2026-10-15', 10, -2)] })
    const wrapper = mount(DailyNetChart, {
      props: { startDate: '2026-10-13', endDate: '2026-10-19', timeframe: '7d' },
    })
    await settle()
    const labels = () => wrapper.findAll('[data-testid="daily-net-legend"] li').map((n) => n.text())
    expect(labels()).toEqual(['Income', 'Expenses', 'Economic net'])

    fetchDailyNet.mockResolvedValue({ status: 'success', data: [dayRow('2026-10-15', 10, -2, 3)] })
    await wrapper.setProps({ endDate: '2026-10-18' })
    await settle()
    expect(labels()).toEqual(['Income', 'Expenses', 'Refunds', 'Economic net'])
  })

  it('only plots 7/30-day trends on daily bars and keeps them out of coarse buckets', async () => {
    fetchDailyNet.mockResolvedValue({ status: 'success', data: [dayRow('2026-10-15', 70, 0)] })
    const daily = mount(DailyNetChart, {
      props: { startDate: '2026-10-13', endDate: '2026-10-19', timeframe: '7d', show7Day: true },
    })
    await settle()
    expect(lastConfig().data.datasets.some((d) => d.label === '7-Day Avg')).toBe(true)
    daily.unmount()

    mount(DailyNetChart, {
      props: { startDate: '2026-01-01', endDate: '2026-10-19', timeframe: 'ytd', show7Day: true, show30Day: true },
    })
    await settle()
    const labels = lastConfig().data.datasets.map((d) => d.label)
    expect(labels).not.toContain('7-Day Avg')
    expect(labels).not.toContain('30-Day Avg')
  })

  it('labels average lines per visible bar period and flags partial buckets', async () => {
    fetchDailyNet.mockResolvedValue({
      status: 'success',
      data: [dayRow('2026-01-10', 100, -20), dayRow('2026-02-10', 300, -40)],
    })
    mount(DailyNetChart, {
      props: { startDate: '2026-01-01', endDate: '2026-02-15', timeframe: 'custom' },
    })
    await settle()
    // 46 days => weekly; averages are per week, not a daily mean.
    const labels = lastConfig().data.datasets.map((d) => d.label)
    expect(labels).not.toContain('Avg Income')

    fetchDailyNet.mockResolvedValue({
      status: 'success',
      data: [dayRow('2026-01-10', 100, -20), dayRow('2026-02-10', 300, -40)],
    })
    mount(DailyNetChart, {
      props: { startDate: '2026-01-01', endDate: '2026-02-15', timeframe: 'ytd', showAvgIncome: true },
    })
    await settle()
    const avg = lastConfig().data.datasets.find((d) => d.label.startsWith('Avg Income'))
    expect(avg.label).toBe('Avg Income / month (incl. partial)')
    expect(avg.data[0]).toBe(200)
  })

  it('compares YTD against the prior calendar year to date with matching day spans', async () => {
    fetchDailyNet
      .mockResolvedValueOnce({ status: 'success', data: [dayRow('2026-02-10', 100, -20)] })
      .mockResolvedValueOnce({
        status: 'success',
        data: [{ date: '2025-01-15', net: money(40) }, { date: '2025-02-10', net: money(10) }],
      })
    const wrapper = mount(DailyNetChart, {
      props: {
        startDate: '2026-01-01',
        endDate: '2026-02-15',
        timeframe: 'ytd',
        showComparisonOverlay: true,
      },
    })
    await settle()
    expect(fetchDailyNet).toHaveBeenLastCalledWith({ start_date: '2025-01-01', end_date: '2025-02-15' })
    const comparison = lastConfig().data.datasets.find((d) => d.label === 'Same period last year')
    // Partial Feb 1-15 pairs with the same 15 days of 2025, not the full prior February.
    expect(comparison.data).toEqual([40, 10])
    expect(wrapper.get('.daily-net-chart__details').text()).toContain('Same period last year: $10.00')
  })

  it('does not block the chart when only the comparison request fails', async () => {
    fetchDailyNet
      .mockResolvedValueOnce({ status: 'success', data: [dayRow('2026-10-15', 10, -2)] })
      .mockRejectedValueOnce(new Error('comparison down'))
    const wrapper = mount(DailyNetChart, {
      props: {
        startDate: '2026-10-13',
        endDate: '2026-10-19',
        timeframe: '7d',
        showComparisonOverlay: true,
      },
    })
    await settle()
    expect(wrapper.find('.daily-net-chart__retry').exists()).toBe(false)
    expect(wrapper.text()).toContain('Comparison data is unavailable')
    expect(lastConfig().data.datasets.some((d) => d.label === 'Previous period')).toBe(false)
  })

  it('ignores a stale response after a fast period switch', async () => {
    const slow = deferred()
    fetchDailyNet
      .mockImplementationOnce(() => slow.promise)
      .mockResolvedValueOnce({ status: 'success', data: [dayRow('2026-10-15', 11, -1)] })
    const wrapper = mount(DailyNetChart, {
      props: { startDate: '2026-01-01', endDate: '2026-10-19', timeframe: '1y' },
    })
    await flushRender()
    await wrapper.setProps({ startDate: '2026-10-13', endDate: '2026-10-19', timeframe: '7d' })
    await settle()
    const summary = wrapper.emitted('summary-change').at(-1)[0]
    expect(summary.totalIncome).toBe(11)

    slow.resolve({ status: 'success', data: [dayRow('2026-03-01', 9999, -1)] })
    await settle()
    expect(wrapper.emitted('summary-change')).toHaveLength(1)
    expect(wrapper.emitted('summary-change').at(-1)[0].totalIncome).toBe(11)
    expect(lastConfig().data.labels).toHaveLength(7)
  })

  it('keeps the toolbar slots mounted and scoped with granularity in empty and error states', async () => {
    fetchDailyNet.mockResolvedValue({ status: 'success', data: [] })
    const wrapper = mount(DailyNetChart, {
      props: { startDate: '2026-01-01', endDate: '2026-10-19', timeframe: 'ytd' },
      slots: {
        title: '<template #title="{ granularityTitle }"><h2>Economic Net · {{ granularityTitle }}</h2></template>',
        controls: '<template #controls="{ granularity }"><button>{{ granularity }}</button></template>',
      },
    })
    await settle()
    expect(wrapper.text()).toContain('No activity in this period')
    expect(wrapper.text()).toContain('Economic Net · Monthly')
    expect(wrapper.get('.daily-net-chart__controls-shell button').text()).toBe('monthly')
  })

  it('coarsens bars one step when the range selector is zoomed out', async () => {
    fetchDailyNet.mockResolvedValue({ status: 'success', data: [dayRow('2026-10-15', 10, -2)] })
    mount(DailyNetChart, {
      props: { startDate: '2026-10-13', endDate: '2026-10-19', timeframe: '7d', zoomedOut: true },
    })
    await settle()
    expect(lastConfig().data.labels).toHaveLength(2)
    expect(fetchDailyNet).toHaveBeenCalledTimes(1)
  })

  it('plots money in and money out on the cash basis and reports cash totals', async () => {
    const cash = (out, inn, debt) => ({
      cash_flow: { money_out: out, money_in: inn, net_cash: inn - out, debt_payment_out: debt },
    })
    fetchDailyNet.mockResolvedValue({
      status: 'success',
      data: [dayRow('2026-10-05', 0, -400, 0, cash(600, 1000, 600))],
    })
    const wrapper = mount(DailyNetChart, {
      props: { startDate: '2026-10-01', endDate: '2026-10-19', timeframe: 'mtd', basis: 'cash' },
    })
    await settle()
    const config = lastConfig()
    const byLabel = Object.fromEntries(config.data.datasets.map((d) => [d.label, d.data]))
    expect(byLabel['Money out'][4]).toBe(-600)
    expect(byLabel['Money in'][4]).toBe(1000)
    expect(byLabel.Expenses).toBeUndefined()
    expect(wrapper.get('[data-testid="daily-net-legend"]').text()).toContain('Net cash movement')
    const summary = wrapper.emitted('summary-change').at(-1)[0]
    expect(summary).toMatchObject({ totalExpenses: -400, totalMoneyOut: 600, totalNetCash: 400 })
  })
})

