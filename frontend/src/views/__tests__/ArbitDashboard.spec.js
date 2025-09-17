// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import ArbitDashboard from '../ArbitDashboard.vue'

const PassThrough = { template: '<div class="pass-through"><slot /></div>' }

const PageHeaderStub = {
  template: '<div class="page-header-stub"><slot name="title" /><slot name="subtitle" /></div>',
}

const createStub = (testId) => ({
  template: `<div data-test="${testId}"></div>`,
})

describe('ArbitDashboard.vue', () => {
  const mountView = () =>
    shallowMount(ArbitDashboard, {
      global: {
        stubs: {
          BasePageLayout: PassThrough,
          PageHeader: PageHeaderStub,
          Card: PassThrough,
          ArbitStatus: createStub('arbit-status-stub'),
          ArbitControls: createStub('arbit-controls-stub'),
          ArbitMetrics: createStub('arbit-metrics-stub'),
          ArbitAlerts: createStub('arbit-alerts-stub'),
          ArbitOpportunities: createStub('arbit-opportunities-stub'),
          ArbitTrades: createStub('arbit-trades-stub'),
        },
      },
    })

  it('renders dashboard sections with expected components', () => {
    const wrapper = mountView()

    const statusSection = wrapper.find('[data-testid="status-controls"]')
    const metricsSection = wrapper.find('[data-testid="metrics-alerts"]')
    const tradesSection = wrapper.find('[data-testid="opportunities-trades"]')

    expect(statusSection.exists()).toBe(true)
    expect(metricsSection.exists()).toBe(true)
    expect(tradesSection.exists()).toBe(true)

    expect(statusSection.find('[data-test="arbit-status-stub"]').exists()).toBe(true)
    expect(statusSection.find('[data-test="arbit-controls-stub"]').exists()).toBe(true)
    expect(metricsSection.find('[data-test="arbit-metrics-stub"]').exists()).toBe(true)
    expect(metricsSection.find('[data-test="arbit-alerts-stub"]').exists()).toBe(true)
    expect(tradesSection.find('[data-test="arbit-opportunities-stub"]').exists()).toBe(true)
    expect(tradesSection.find('[data-test="arbit-trades-stub"]').exists()).toBe(true)
  })

  it('matches snapshot', () => {
    const wrapper = mountView()
    expect(wrapper.html()).toMatchSnapshot()
  })
})
