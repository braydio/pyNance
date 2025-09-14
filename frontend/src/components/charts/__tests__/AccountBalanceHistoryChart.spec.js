// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import AccountBalanceHistoryChart from '../AccountBalanceHistoryChart.vue'

// Stub canvas context
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({}))

const destroyMock = vi.fn()
vi.mock('chart.js/auto', () => {
  const Chart = vi.fn().mockImplementation(() => ({ destroy: destroyMock }))
  Chart.getChart = vi.fn().mockReturnValue(null)
  return { Chart }
})
import { Chart as ChartConstructor } from 'chart.js/auto'

describe('AccountBalanceHistoryChart.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows empty state when no history data', async () => {
    const wrapper = shallowMount(AccountBalanceHistoryChart, {
      props: { historyData: [], selectedRange: '30d' },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('No history available for this period')
    expect(ChartConstructor).not.toHaveBeenCalled()
  })

  it('re-renders chart when history data changes', async () => {
    const wrapper = shallowMount(AccountBalanceHistoryChart, {
      props: {
        historyData: [{ date: '2024-01-01', balance: 10 }],
        selectedRange: '30d',
      },
    })
    await flushPromises()
    expect(ChartConstructor).toHaveBeenCalledTimes(1)

    await wrapper.setProps({ historyData: [{ date: '2024-02-01', balance: 20 }] })
    await flushPromises()
    expect(ChartConstructor).toHaveBeenCalledTimes(2)
  })

  it('re-renders chart when selectedRange changes', async () => {
    const wrapper = shallowMount(AccountBalanceHistoryChart, {
      props: {
        historyData: [{ date: '2024-01-01', balance: 10 }],
        selectedRange: '30d',
      },
    })
    await flushPromises()
    expect(ChartConstructor).toHaveBeenCalledTimes(1)

    await wrapper.setProps({ selectedRange: '60d' })
    await flushPromises()
    expect(ChartConstructor).toHaveBeenCalledTimes(2)
  })
})
