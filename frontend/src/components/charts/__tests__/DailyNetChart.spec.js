// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import DailyNetChart from '../DailyNetChart.vue'
import { fetchDailyNet } from '@/api/charts'

const chartMock = vi.fn()

vi.mock('chart.js/auto', () => ({
  Chart: vi.fn().mockImplementation((_ctx, config) => {
    chartMock(config)
    return {
      destroy: vi.fn(),
      data: config.data,
      getElementsAtEventForMode: vi.fn().mockReturnValue([]),
      getDatasetMeta: vi.fn().mockReturnValue({ data: [] }),
    }
  }),
}))

vi.mock('@/api/charts', () => ({
  fetchDailyNet: vi.fn(),
}))

/**
 * Format a Date object as YYYY-MM-DD for chart expectations.
 *
 * @param {Date} date - Date to format.
 * @returns {string} ISO-like date string.
 */
function formatDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Flush pending promises and Vue renders.
 *
 * @returns {Promise<void>} Promise resolved after queued microtasks.
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
    mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
      },
    })

    await flushRender()
    await flushRender()

    const lastConfig = chartMock.mock.calls[chartMock.mock.calls.length - 1][0]
    const labels = lastConfig.data.labels

    expect(labels).toHaveLength(30)
    expect(labels[0]).toBe('2024-06-01')
    expect(labels[29]).toBe('2024-06-30')

    const incomeDataset = lastConfig.data.datasets.find((dataset) => dataset.label === 'Income')
    const expenseDataset = lastConfig.data.datasets.find((dataset) => dataset.label === 'Expenses')
    const netDataset = lastConfig.data.datasets.find((dataset) => dataset.label === 'Net')

    expect(incomeDataset.data).toHaveLength(30)
    expect(expenseDataset.data).toHaveLength(30)
    expect(netDataset.data).toHaveLength(30)

    const juneFirstIndex = labels.indexOf('2024-06-01')
    expect(incomeDataset.data[juneFirstIndex]).toBe(0)
    expect(expenseDataset.data[juneFirstIndex]).toBe(0)
    expect(netDataset.data[juneFirstIndex]).toBe(0)

    const juneSecondIndex = labels.indexOf('2024-06-02')
    expect(incomeDataset.data[juneSecondIndex]).toBe(100)

    const juneLastIndex = labels.indexOf('2024-06-30')
    expect(incomeDataset.data[juneLastIndex]).toBe(0)
    expect(expenseDataset.data[juneLastIndex]).toBe(0)
  })

  it('keeps labels aligned to the month of the selected start date', async () => {
    const referenceDate = new Date('2024-02-10T00:00:00')
    const expectedStart = formatDateKey(new Date(referenceDate.getFullYear(), 1, 1))
    const expectedEnd = formatDateKey(new Date(referenceDate.getFullYear(), 2, 0))

    mount(DailyNetChart, {
      props: {
        startDate: formatDateKey(referenceDate),
        endDate: formatDateKey(new Date(referenceDate.getFullYear(), 1, 29)),
        zoomedOut: false,
      },
    })

    await flushRender()
    await flushRender()

    const lastConfig = chartMock.mock.calls[chartMock.mock.calls.length - 1][0]
    const labels = lastConfig.data.labels

    expect(labels[0]).toBe(expectedStart)
    expect(labels[labels.length - 1]).toBe(expectedEnd)
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
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-05-02',
            income: { parsedValue: 90 },
            expenses: { parsedValue: -35 },
            net: { parsedValue: 55 },
            transaction_count: 1,
          },
          {
            date: '2024-05-15',
            income: { parsedValue: 210 },
            expenses: { parsedValue: -90 },
            net: { parsedValue: 120 },
            transaction_count: 4,
          },
        ],
      })

    mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
        showComparisonOverlay: true,
        comparisonMode: 'prior_month_to_date',
      },
    })

    await flushRender()
    await flushRender()

    const lastConfig = chartMock.mock.calls[chartMock.mock.calls.length - 1][0]
    const labels = lastConfig.data.labels
    const comparisonDataset = lastConfig.data.datasets.find(
      (dataset) => dataset.label === 'Prior month to-date',
    )

    expect(comparisonDataset).toBeTruthy()

    const juneSecondIndex = labels.indexOf('2024-06-02')
    const juneFifteenthIndex = labels.indexOf('2024-06-15')

    expect(comparisonDataset.data[juneSecondIndex]).toBe(55)
    expect(comparisonDataset.data[juneFifteenthIndex]).toBe(120)
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
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          {
            date: '2024-05-02',
            income: { parsedValue: 90 },
            expenses: { parsedValue: -35 },
            net: { parsedValue: 55 },
            transaction_count: 1,
          },
        ],
      })

    const wrapper = mount(DailyNetChart, {
      props: {
        startDate: '2024-06-01',
        endDate: '2024-06-30',
        zoomedOut: false,
        showComparisonOverlay: true,
        comparisonMode: 'prior_month_to_date',
      },
    })

    await flushRender()
    await flushRender()

    let lastConfig = chartMock.mock.calls[chartMock.mock.calls.length - 1][0]
    expect(
      lastConfig.data.datasets.some((dataset) => dataset.label === 'Prior month to-date'),
    ).toBe(true)

    await wrapper.setProps({ showComparisonOverlay: false })
    await flushRender()
    await flushRender()

    lastConfig = chartMock.mock.calls[chartMock.mock.calls.length - 1][0]
    expect(
      lastConfig.data.datasets.some((dataset) => dataset.label === 'Prior month to-date'),
    ).toBe(false)
  })
})
