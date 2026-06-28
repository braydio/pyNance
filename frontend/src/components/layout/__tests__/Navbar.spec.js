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
})
