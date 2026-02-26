// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AppLayout from '../AppLayout.vue'

describe('AppLayout', () => {
  it('renders header, centered main wrapper, and footer slots', () => {
    const wrapper = mount(AppLayout, {
      slots: {
        header: '<div id="header-slot">Header</div>',
        default: '<div id="main-slot">Main content</div>',
        footer: '<div id="footer-slot">Footer</div>',
      },
    })

    expect(wrapper.find('header #header-slot').exists()).toBe(true)
    expect(wrapper.find('main #main-slot').exists()).toBe(true)
    expect(wrapper.find('footer #footer-slot').exists()).toBe(true)

    const mainContainer = wrapper.find('main > div')
    expect(mainContainer.classes()).toContain('mx-auto')
    expect(mainContainer.classes()).toContain('w-full')
    expect(mainContainer.classes()).toContain('max-w-7xl')
  })

  it('omits the header element when no header slot is provided', () => {
    const wrapper = mount(AppLayout, {
      slots: {
        default: '<div>Main content</div>',
        footer: '<div>Footer content</div>',
      },
    })

    expect(wrapper.find('header').exists()).toBe(false)
  })
})
