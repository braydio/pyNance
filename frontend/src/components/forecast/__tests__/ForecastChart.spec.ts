// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { beforeAll, describe, expect, it, vi } from 'vitest'
import ForecastChart from '../ForecastChart.vue'

vi.mock('chart.js', () => ({
  Chart: Object.assign(
    vi.fn().mockImplementation(() => ({ destroy: vi.fn() })),
    { register: vi.fn() },
  ),
  registerables: [],
}))

beforeAll(() => {
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
    canvas: document.createElement('canvas'),
  }))
})

const baseProps = {
  viewType: 'Month',
  graphMode: 'combined',
  realizedHistory: [{ label: 'H1', balance: 90 }],
  timeline: [{ label: 'F1', forecast_balance: 100, actual_balance: null }],
  computeMeta: {
    lookbackDays: 90,
    movingAverageWindow: 30,
    normalize: false,
    includesAutoDetectedAdjustments: true,
    autoDetectedAdjustmentCount: 2,
  },
}

describe('ForecastChart', () => {
  it('renders the chart canvas and methodology help text', () => {
    const wrapper = mount(ForecastChart, {
      props: baseProps,
    })

    expect(wrapper.find('canvas').exists()).toBe(true)
    expect(wrapper.text()).toContain('How this forecast is calculated')
    expect(wrapper.text()).toContain('latest 90 days of realized history')
    expect(wrapper.text()).toContain('30-day moving average')
    expect(wrapper.text()).toContain('Normalization is off')
    expect(wrapper.text()).toContain('Auto-detected adjustments are included (2 detected)')
  })

  it('updates methodology help text when compute controls change', async () => {
    const wrapper = mount(ForecastChart, {
      props: baseProps,
    })

    await wrapper.setProps({
      graphMode: 'forecast',
      computeMeta: {
        lookbackDays: 60,
        movingAverageWindow: 7,
        normalize: true,
        includesAutoDetectedAdjustments: false,
        autoDetectedAdjustmentCount: 0,
      },
    })

    expect(wrapper.text()).toContain('latest 60 days of realized history')
    expect(wrapper.text()).toContain('7-day moving average')
    expect(wrapper.text()).toContain('renders in forecast mode')
    expect(wrapper.text()).toContain('Normalization is on')
    expect(wrapper.text()).toContain('Auto-detected adjustments are not included')
  })

  it('emits a view update when toggled', async () => {
    const wrapper = mount(ForecastChart, {
      props: baseProps,
    })

    await wrapper.get('.toggle-button').trigger('click')

    expect(wrapper.emitted('update:viewType')).toEqual([['Year']])
  })
})
