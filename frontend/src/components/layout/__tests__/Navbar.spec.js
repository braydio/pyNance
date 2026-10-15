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

  describe('small-screen scrolling row', () => {
    const mountNav = () =>
      mount(Navbar, {
        attachTo: document.body,
        global: {
          stubs: {
            RouterLink: {
              props: ['to'],
              template:
                '<a :href="to" :class="{ \'router-link-exact-active\': to === \'/forecast\' }"><slot /></a>',
            },
            Moon: true,
            Sun: true,
            Settings: true,
          },
        },
      })

    function setScrollMetrics(el, { scrollWidth, clientWidth, scrollLeft }) {
      Object.defineProperty(el, 'scrollWidth', { configurable: true, value: scrollWidth })
      Object.defineProperty(el, 'clientWidth', { configurable: true, value: clientWidth })
      el.scrollLeft = scrollLeft
    }

    it('shows an end fade only while more links are hidden, then a start fade after scrolling', async () => {
      const wrapper = mountNav()
      const row = wrapper.get('[data-testid="nav-links"]')
      setScrollMetrics(row.element, { scrollWidth: 600, clientWidth: 300, scrollLeft: 0 })
      await row.trigger('scroll')
      expect(row.classes()).toContain('nav-links--fade-end')
      expect(row.classes()).not.toContain('nav-links--fade-start')

      setScrollMetrics(row.element, { scrollWidth: 600, clientWidth: 300, scrollLeft: 150 })
      await row.trigger('scroll')
      expect(row.classes()).toEqual(
        expect.arrayContaining(['nav-links--fade-start', 'nav-links--fade-end']),
      )

      setScrollMetrics(row.element, { scrollWidth: 600, clientWidth: 300, scrollLeft: 300 })
      await row.trigger('scroll')
      expect(row.classes()).not.toContain('nav-links--fade-end')
      wrapper.unmount()
    })

    it('keeps the current destination scrolled into view and no fade when everything fits', async () => {
      const calls = []
      const original = HTMLElement.prototype.scrollIntoView
      HTMLElement.prototype.scrollIntoView = function (options) {
        calls.push([this.getAttribute('href'), options])
      }
      const wrapper = mountNav()
      await wrapper.vm.$nextTick()
      await wrapper.vm.$nextTick()
      expect(calls.at(-1)[0]).toBe('/forecast')
      expect(calls.at(-1)[1]).toMatchObject({ inline: 'center' })
      expect(wrapper.get('[data-testid="nav-links"]').classes()).not.toContain(
        'nav-links--fade-end',
      )
      HTMLElement.prototype.scrollIntoView = original
      wrapper.unmount()
    })
  })
})
