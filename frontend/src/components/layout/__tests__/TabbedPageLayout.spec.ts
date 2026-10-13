// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import TabbedPageLayout from '../TabbedPageLayout.vue'

function mountLayout(props = {}) {
  return mount(TabbedPageLayout, {
    attachTo: document.body,
    props: {
      tabs: ['One', { label: 'Two', slot: 'Two', disabled: true }, 'Three'],
      modelValue: 'One',
      sidebarWidth: 'w-72 md:w-80',
      ...props,
    },
    slots: {
      One: '<p>one</p>',
      Three: '<p>three</p>',
      sidebar: '<div class="side">side</div>',
    },
  })
}

describe('TabbedPageLayout', () => {
  it('stacks the sidebar below content on narrow screens and goes side-by-side at lg', () => {
    const wrapper = mountLayout()
    const row = wrapper.get('.lg\\:flex-row')
    expect(row.classes()).toEqual(expect.arrayContaining(['flex-col', 'lg:flex-row']))
    const aside = wrapper.get('[data-testid="tabbed-sidebar"]')
    expect(aside.classes()).toEqual(expect.arrayContaining(['max-lg:w-full', 'w-72', 'md:w-80']))
  })

  it('exposes tab semantics and a labelled panel', () => {
    const wrapper = mountLayout()
    expect(wrapper.get('[role="tablist"]').exists()).toBe(true)
    const tabs = wrapper.findAll('[role="tab"]')
    expect(tabs.map((tab) => tab.attributes('aria-selected'))).toEqual(['true', 'false', 'false'])
    expect(tabs[0].attributes('tabindex')).toBe('0')
    expect(tabs[2].attributes('tabindex')).toBe('-1')
    expect(wrapper.get('[role="tabpanel"]').attributes('aria-labelledby')).toBe('tab-One')
  })

  it('moves between enabled tabs with arrow keys, skipping disabled ones', async () => {
    const wrapper = mountLayout()
    await wrapper.findAll('[role="tab"]')[0].trigger('keydown', { key: 'ArrowRight' })
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['Three'])
  })
})
