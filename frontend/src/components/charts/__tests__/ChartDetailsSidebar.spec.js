// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChartDetailsSidebar from '../ChartDetailsSidebar.vue'

describe('ChartDetailsSidebar', () => {
  it('applies shared accent utility class to the overlay options trigger', () => {
    const wrapper = mount(ChartDetailsSidebar)

    const overlayTrigger = wrapper.get('button.chart-details-sidebar__toggle')
    expect(overlayTrigger.classes()).toContain('accent-toggle-btn')
  })
})

describe('ChartDetailsSidebar granularity', () => {
  const trendInputs = (wrapper) =>
    wrapper.findAll('input[type="checkbox"]').filter((input) => {
      const text = input.element.parentElement.textContent
      return /Day Trended/.test(text)
    })

  it('enables 7/30-day trends on daily bars', () => {
    const wrapper = mount(ChartDetailsSidebar, { props: { granularity: 'daily' } })
    const inputs = trendInputs(wrapper)
    expect(inputs).toHaveLength(2)
    inputs.forEach((input) => expect(input.attributes('disabled')).toBeUndefined())
    expect(wrapper.find('[data-testid="daily-overlay-reason"]').exists()).toBe(false)
  })

  it.each(['weekly', 'monthly', 'quarterly'])(
    'disables 7/30-day trends with a reason on %s bars',
    (granularity) => {
      const wrapper = mount(ChartDetailsSidebar, { props: { granularity } })
      trendInputs(wrapper).forEach((input) => expect(input.attributes('disabled')).toBeDefined())
      expect(wrapper.get('[data-testid="daily-overlay-reason"]').text()).toContain('daily bars only')
    },
  )

  it('words the average toggles per visible bar period', () => {
    const wrapper = mount(ChartDetailsSidebar, { props: { granularity: 'monthly' } })
    expect(wrapper.text()).toContain('Avg Income per month')
    expect(wrapper.text()).toContain('Avg Expenses per month')
  })
})
