// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import ForecastChart from '../ForecastChart.vue'

vi.mock('chart.js', () => ({
  Chart: Object.assign(
    vi.fn().mockImplementation(() => ({ destroy: vi.fn() })),
    { register: vi.fn() },
  ),
  registerables: [],
}))

describe('ForecastChart graph modes', () => {
  it('renders in combined mode', () => {
    const wrapper = mount(ForecastChart, {
      props: {
        viewType: 'Month',
        graphMode: 'combined',
        realizedHistory: [{ label: 'H1', balance: 90 }],
        timeline: [{ label: 'F1', forecast_balance: 100, actual_balance: null }],
      },
    })
    expect(wrapper.find('canvas').exists()).toBe(true)
  })
})
