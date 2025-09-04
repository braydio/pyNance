// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { RouterLink } from 'vue-router'
import AppFooter from '../AppFooter.vue'
import pkg from '../../../../package.json' with { type: 'json' }

describe('AppFooter', () => {
  it('renders footer links and version', () => {
    const wrapper = mount(AppFooter, {
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })
    const links = wrapper.findAll('a')
    expect(links).toHaveLength(3)
    expect(links[0].text()).toBe('Settings')
    expect(links[1].text()).toBe('Docs')
    expect(links[2].text()).toBe('Support')
    expect(wrapper.text()).toContain(`v${pkg.version}`)
  })
})
