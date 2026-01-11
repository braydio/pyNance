// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import DailySpendingPanel from '../DailySpendingPanel.vue'
import * as chartsApi from '@/api/charts'
import * as transactionsApi from '@/api/transactions'
import { Chart } from 'chart.js/auto'

HTMLCanvasElement.prototype.getContext = vi.fn(() => ({}))

let chartConfig
const mockChartInstance = { destroy: vi.fn() }

vi.mock('chart.js/auto', () => {
  const Chart = vi.fn((ctx, config) => {
    chartConfig = config
    return mockChartInstance
  })
  Chart.getChart = vi.fn().mockReturnValue(null)
  return { Chart }
})

vi.mock('@/api/charts', () => ({
  fetchCategoryBreakdownTree: vi.fn(),
}))

vi.mock('@/api/transactions', () => ({
  fetchTransactions: vi.fn(),
}))

describe('DailySpendingPanel', () => {
  beforeEach(() => {
    chartConfig = null
    chartsApi.fetchCategoryBreakdownTree.mockReset()
    transactionsApi.fetchTransactions.mockReset()
  })

  afterEach(() => {
    Chart.mockClear()
  })

  it('renders category totals and transaction rows on success', async () => {
    chartsApi.fetchCategoryBreakdownTree.mockResolvedValue({
      status: 'success',
      data: [
        { id: 'food', label: 'Food', amount: 25 },
        { id: 'fuel', label: 'Fuel', amount: 10 },
      ],
    })
    transactionsApi.fetchTransactions.mockResolvedValue({
      transactions: [
        { transaction_id: 't1', date: '2024-06-02', amount: -12.5, name: 'Coffee' },
        { transaction_id: 't2', date: '2024-06-03', amount: -5, merchant_name: 'Cafe' },
      ],
    })

    const wrapper = mount(DailySpendingPanel, {
      props: { detailDate: '2024-06-03', minDetailDate: '2024-06-01' },
    })

    await flushPromises()

    expect(chartsApi.fetchCategoryBreakdownTree).toHaveBeenCalledWith({
      start_date: '2024-06-03',
      end_date: '2024-06-03',
    })
    expect(transactionsApi.fetchTransactions).toHaveBeenCalledWith({
      start_date: '2024-06-03',
      end_date: '2024-06-03',
      page_size: 6,
    })
    expect(chartConfig.data.labels).toEqual(['Today'])
    expect(chartConfig.data.datasets.map((dataset) => dataset.label)).toEqual(['Food', 'Fuel'])

    const rows = wrapper.findAll('.transaction-row')
    expect(rows[0].text()).toContain('Cafe')
    expect(rows[1].text()).toContain('Coffee')
  })

  it('shows empty states when no data is returned', async () => {
    chartsApi.fetchCategoryBreakdownTree.mockResolvedValue({
      status: 'success',
      data: [],
    })
    transactionsApi.fetchTransactions.mockResolvedValue({
      transactions: [],
    })

    const wrapper = mount(DailySpendingPanel, {
      props: { detailDate: '2024-06-03', minDetailDate: '2024-06-01' },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('No spending yet today.')
    expect(wrapper.text()).toContain('No transactions found.')
  })

  it('renders the average overlay only when the toggle is enabled', async () => {
    chartsApi.fetchCategoryBreakdownTree
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          { id: 'food', label: 'Food', amount: 30 },
          { id: 'fuel', label: 'Fuel', amount: 12 },
        ],
      })
      .mockResolvedValueOnce({
        status: 'success',
        data: [
          { id: 'food', label: 'Food', amount: 90 },
          { id: 'fuel', label: 'Fuel', amount: 24 },
        ],
      })
    transactionsApi.fetchTransactions.mockResolvedValue({ transactions: [] })

    const wrapper = mount(DailySpendingPanel, {
      props: { detailDate: '2024-06-03', minDetailDate: '2024-06-01' },
    })

    await flushPromises()

    expect(chartConfig.data.datasets.some((dataset) => dataset.label.includes('(Avg)'))).toBe(false)

    await wrapper.get('input[type="checkbox"]').setValue(true)
    await flushPromises()

    const averageDataset = chartConfig.data.datasets.find((dataset) => dataset.label === 'Food (Avg)')
    expect(averageDataset.data).toEqual([30])
  })

  it('skips the average overlay when the date range is empty', async () => {
    chartsApi.fetchCategoryBreakdownTree.mockResolvedValue({
      status: 'success',
      data: [{ id: 'food', label: 'Food', amount: 20 }],
    })
    transactionsApi.fetchTransactions.mockResolvedValue({ transactions: [] })

    const wrapper = mount(DailySpendingPanel, {
      props: { detailDate: '2024-06-01', minDetailDate: '2024-06-02' },
    })

    await flushPromises()

    await wrapper.get('input[type="checkbox"]').setValue(true)
    await flushPromises()

    expect(chartsApi.fetchCategoryBreakdownTree).toHaveBeenCalledTimes(1)
    expect(chartConfig.data.datasets.some((dataset) => dataset.label.includes('(Avg)'))).toBe(false)
  })
})
