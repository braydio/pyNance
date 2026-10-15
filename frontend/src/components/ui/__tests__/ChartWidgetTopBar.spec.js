// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChartWidgetTopBar from '../ChartWidgetTopBar.vue'

describe('ChartWidgetTopBar', () => {
  const mountBar = () =>
    mount(ChartWidgetTopBar, {
      slots: {
        title: 'Net Income',
        controls: '<button type="button">A</button><button type="button">B</button>',
        summary: '<span>Income $1,000,000.00 · Expenses $999,999.99</span>',
      },
    })

  it('lets controls wrap independently of the title instead of pushing past the viewport', () => {
    const wrapper = mountBar()
    const controls = wrapper.findAll('div').find((d) => d.text() === 'AB')
    expect(controls.classes()).toEqual(
      expect.arrayContaining(['flex-wrap', 'min-w-0', 'max-w-full']),
    )
    expect(controls.classes()).not.toContain('flex-shrink-0')
    expect(wrapper.get('h2').classes()).toContain('truncate')
  })

  it('does not force a fixed minimum width on the summary at narrow widths', () => {
    const wrapper = mountBar()
    const summary = wrapper.get('.chart-summary')
    expect(summary.classes()).toEqual(expect.arrayContaining(['max-w-full', 'min-w-0']))
    expect(summary.classes().join(' ')).not.toMatch(/min-w-\[/)
  })
})
