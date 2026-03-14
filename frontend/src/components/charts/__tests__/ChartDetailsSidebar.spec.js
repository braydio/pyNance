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
