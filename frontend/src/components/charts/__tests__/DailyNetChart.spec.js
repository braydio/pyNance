// @vitest-environment jsdom
/**
 * Component tests for DailyNetChart date padding and moving averages.
 */
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

  it('keeps labels aligned to the selected date range', async () => {
    const referenceDate = new Date('2024-02-10T00:00:00')
    const expectedStart = formatDateKey(referenceDate)
    const expectedEnd = formatDateKey(new Date(referenceDate.getFullYear(), 1, 29))

    mount(DailyNetChart, {
      props: {
        startDate: formatDateKey(referenceDate),
        endDate: expectedEnd,
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
          date: '2024-03-07',
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
        endDate: '2024-03-07',
        zoomedOut: false,
        show7Day: true,
      },
    })

    await flushRender()
    await flushRender()

    const lastConfig = chartMock.mock.calls[chartMock.mock.calls.length - 1][0]
    const labels = lastConfig.data.labels

    expect(labels).toHaveLength(7)
    expect(labels[0]).toBe('2024-03-01')
    expect(labels[6]).toBe('2024-03-07')

    const incomeDataset = lastConfig.data.datasets.find((dataset) => dataset.label === 'Income')
    const movingAverageDataset = lastConfig.data.datasets.find(
      (dataset) => dataset.label === '7-Day Avg',
    )

    expect(incomeDataset.data[1]).toBe(0)
    expect(movingAverageDataset.data[0]).toBeCloseTo(10, 5)
    expect(movingAverageDataset.data[5]).toBeCloseTo(10, 5)
    expect(movingAverageDataset.data[6]).toBeCloseTo(20, 5)
  })
})
