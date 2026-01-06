// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { Chart } from 'chart.js/auto'
import CategoryBreakdownChart from '../CategoryBreakdownChart.vue'
import * as chartsApi from '@/api/charts'

// Stub canvas context
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({}))

// Capture onClick handler from chart config
let clickHandler
const mockChartInstance = {
  destroy: vi.fn(),
  getElementsAtEventForMode: vi.fn().mockReturnValue([{ index: 0 }]),
  data: {},
}

vi.mock('chart.js/auto', () => {
  const Chart = vi.fn().mockImplementation((ctx, cfg) => {
    clickHandler = cfg.options.onClick
    mockChartInstance.data = cfg.data
    return mockChartInstance
  })
  Chart.getChart = vi.fn().mockReturnValue(null)
  return { Chart }
})

vi.mock('@/api/charts', () => ({
  fetchCategoryBreakdownTree: vi.fn().mockResolvedValue({
    status: 'success',
    data: [
      {
        id: 'p1',
        label: 'Parent',
        amount: 100,
        children: [
          { id: 'c1', label: 'Child 1', amount: 60 },
          { id: 'c2', label: 'Child 2', amount: 40 },
        ],
      },
    ],
  }),
  fetchMerchantBreakdown: vi.fn().mockResolvedValue({
    status: 'success',
    data: [{ label: 'Merchant One', amount: 42.5 }],
  }),
}))

describe('CategoryBreakdownChart.vue', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    chartsApi.fetchCategoryBreakdownTree.mockClear()
    chartsApi.fetchMerchantBreakdown.mockClear()
  })

  afterEach(() => {
    vi.useRealTimers()
    Chart.mockClear()
  })

  it('emits only selected category IDs on bar click', async () => {
    const wrapper = shallowMount(CategoryBreakdownChart, {
      props: {
        startDate: '2024-01-01',
        endDate: '2024-01-31',
        selectedCategoryIds: ['c1'],
        groupOthers: false,
      },
    })

    await flushPromises()

    // Simulate chart click
    clickHandler(new Event('click'))

    const emitted = wrapper.emitted('bar-click')
    expect(emitted).toBeTruthy()
    expect(emitted[0][0]).toEqual({ label: 'Child 1', ids: ['c1'] })
  })

  it('debounces range-driven fetches to a single call', async () => {
    const wrapper = shallowMount(CategoryBreakdownChart, {
      props: {
        startDate: '2024-01-01',
        endDate: '2024-01-31',
        selectedCategoryIds: ['c1'],
        groupOthers: true,
      },
    })

    await flushPromises()
    chartsApi.fetchCategoryBreakdownTree.mockClear()

    await wrapper.setProps({ startDate: '2024-02-01' })
    await wrapper.setProps({ endDate: '2024-02-15', groupOthers: false })
    await vi.advanceTimersByTimeAsync(210)
    await flushPromises()

    expect(chartsApi.fetchCategoryBreakdownTree).toHaveBeenCalledTimes(1)
  })

  it('loads merchant breakdown data when requested', async () => {
    const wrapper = shallowMount(CategoryBreakdownChart, {
      props: {
        startDate: '2024-01-01',
        endDate: '2024-01-31',
        selectedCategoryIds: ['Merchant One'],
        groupOthers: false,
        breakdownType: 'merchant',
      },
    })

    await flushPromises()

    expect(chartsApi.fetchMerchantBreakdown).toHaveBeenCalled()
    expect(mockChartInstance.data.labels).toEqual(['Merchant One'])
    wrapper.unmount()
  })

  it('refreshes the chart after debounced selection updates', async () => {
    const wrapper = shallowMount(CategoryBreakdownChart, {
      props: {
        startDate: '2024-01-01',
        endDate: '2024-01-31',
        selectedCategoryIds: ['c1'],
        groupOthers: false,
      },
    })

    await flushPromises()
    Chart.mockClear()

    await wrapper.setProps({ selectedCategoryIds: ['c1', 'c2'] })
    await vi.advanceTimersByTimeAsync(220)
    await flushPromises()

    expect(Chart).toHaveBeenCalledTimes(1)
    expect(mockChartInstance.data.labels).toEqual(['Child 1', 'Child 2'])
  })
})
