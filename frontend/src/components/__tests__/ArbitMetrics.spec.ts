// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import ArbitMetrics from '../ArbitMetrics.vue'

vi.mock('@/services/arbit', () => ({
  fetchArbitMetrics: vi.fn().mockResolvedValue({
    profit: [{ label: 'p', value: 1 }],
    latency: [{ label: 'l', value: 2 }],
  }),
}))

describe('ArbitMetrics.vue', () => {
  it('renders charts with metrics', async () => {
    const wrapper = mount(ArbitMetrics, {
      global: {
        stubs: {
          PortfolioAllocationChart: {
            props: ['allocations'],
            template: '<div class="chart">{{ allocations.length }}</div>',
          },
        },
      },
    })
    await flushPromises()
    const charts = wrapper.findAll('.chart')
    expect(charts).toHaveLength(2)
    expect(charts[0].text()).toBe('1')
    expect(charts[1].text()).toBe('1')
  })
})
