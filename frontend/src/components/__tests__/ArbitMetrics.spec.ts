// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import ArbitMetrics from '../ArbitMetrics.vue'

vi.mock('@/services/arbit', () => ({
  fetchArbitMetrics: vi.fn().mockResolvedValue({
    profit: [{ label: 'Total Profit ($)', value: 1 }],
    latency: [{ label: 'Cycle Latency (s)', value: 2 }],
  }),
}))

describe('ArbitMetrics.vue', () => {
  it('renders charts with metrics', async () => {
    const wrapper = mount(ArbitMetrics, {
      global: {
        stubs: {
          PortfolioAllocationChart: {
            props: ['allocations'],
            template:
              '<div class="chart">{{ allocations[0].label }}:{{ allocations[0].value }}</div>',
          },
        },
      },
    })
    await flushPromises()
    const charts = wrapper.findAll('.chart')
    expect(charts).toHaveLength(2)
    expect(charts[0].text()).toBe('Total Profit ($):1')
    expect(charts[1].text()).toBe('Cycle Latency (s):2')
  })
})
