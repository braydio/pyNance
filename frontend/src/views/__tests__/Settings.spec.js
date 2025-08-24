// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import SettingsView from '../Settings.vue'

vi.mock('axios', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { themes: [], current_theme: '' } }),
    post: vi.fn().mockResolvedValue({})
  }
}))

describe('Settings.vue', () => {
  it('matches snapshot', async () => {
    const wrapper = shallowMount(SettingsView, {
      global: {
        stubs: ['BasePageLayout', 'PageHeader', 'SettingsIcon']
      }
    })
    await flushPromises()
    expect(wrapper.html()).toMatchSnapshot()
  })
})
