// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import CategoryBreakdownChart from '../CategoryBreakdownChart.vue'

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
}))

describe('CategoryBreakdownChart.vue', () => {
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
    expect(emitted[0][0]).toEqual({ label: 'Parent', ids: ['c1'] })
  })
})
