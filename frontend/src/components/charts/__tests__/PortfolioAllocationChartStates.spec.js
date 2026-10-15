// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'

vi.mock('chart.js/auto', () => ({
  Chart: vi.fn().mockImplementation(() => ({ destroy: vi.fn() })),
}))

import PortfolioAllocationChart from '../PortfolioAllocationChart.vue'

describe('PortfolioAllocationChart states', () => {
  it('shows an empty state instead of a blank canvas when there is nothing to chart', () => {
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({}))
    const wrapper = mount(PortfolioAllocationChart, { props: { allocations: [] } })
    expect(wrapper.get('[data-testid="allocation-empty"]').text()).toContain('No allocation data')
    expect(wrapper.find('[data-testid="allocation-summary-list"]').exists()).toBe(false)
  })

  it('describes the chart for assistive technology when data exists', () => {
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({}))
    const wrapper = mount(PortfolioAllocationChart, {
      props: {
        allocations: [
          { label: 'Equity', value: 1500 },
          { label: 'Cash', value: 500 },
        ],
      },
    })
    const canvas = wrapper.get('canvas')
    expect(canvas.attributes('role')).toBe('img')
    expect(canvas.attributes('aria-label')).toContain('Equity $1,500.00')
    expect(wrapper.find('[data-testid="allocation-empty"]').exists()).toBe(false)
    expect(wrapper.get('[data-testid="allocation-summary-list"]').text()).toContain('Cash')
  })
})
