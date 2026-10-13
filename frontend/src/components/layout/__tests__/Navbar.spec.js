// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import Navbar from '../Navbar.vue'
import { setTheme } from '@/composables/useTheme'

describe('Navbar', () => {
  beforeEach(() => {
    localStorage.clear()
    setTheme('nightfox')
  })

  it('toggles between the dark and light themes', async () => {
    const wrapper = mount(Navbar, {
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
          Moon: true,
          Sun: true,
        },
      },
    })

    const toggle = wrapper.get('.theme-toggle')
    expect(toggle.attributes('aria-label')).toContain('Everforest')

    await toggle.trigger('click')

    expect(document.documentElement.dataset.theme).toBe('everforest-light')
    expect(toggle.attributes('aria-label')).toContain('Nightfox')
  })

  it('links every primary destination plus a secondary Settings entry', () => {
    const wrapper = mount(Navbar, {
      global: {
        stubs: {
          RouterLink: {
            props: ['to'],
            template: '<a :href="to"><slot /></a>',
          },
          Moon: true,
          Sun: true,
          Settings: true,
        },
      },
    })

    const primary = wrapper.findAll('.nav-links a').map((a) => [a.attributes('href'), a.text()])
    expect(primary).toEqual([
      ['/', 'Dashboard'],
      ['/accounts', 'Accounts'],
      ['/transactions', 'Transactions'],
      ['/forecast', 'Forecast'],
      ['/planning', 'Planning'],
      ['/investments', 'Investments'],
    ])
    const settings = wrapper.get('a[href="/settings"]')
    expect(settings.attributes('aria-label')).toBe('Settings')
    expect(wrapper.find('.nav-links a[href="/settings"]').exists()).toBe(false)
    expect(wrapper.get('nav').attributes('aria-label')).toBe('Primary navigation')
  })
})
