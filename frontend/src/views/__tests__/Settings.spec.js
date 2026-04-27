// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import SettingsView from '../Settings.vue'

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
      get: vi.fn(),
      post: vi.fn(),
    })),
    get: vi.fn().mockResolvedValue({ data: { themes: [], current_theme: '' } }),
    post: vi.fn().mockResolvedValue({}),
  },
}))

describe('Settings.vue', () => {
  it('renders settings sections and refresh controls', async () => {
    const wrapper = shallowMount(SettingsView, {
      global: {
        stubs: {
          BasePageLayout: {
            template: '<div><slot /></div>',
          },
          PageHeader: {
            template: '<div><slot name="title" /><slot name="subtitle" /></div>',
          },
          SettingsIcon: true,
          RefreshPlaidControls: true,
        },
      },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Appearance')
    expect(wrapper.text()).toContain('Connected Accounts')
    expect(wrapper.find('refresh-plaid-controls-stub').exists()).toBe(true)
  })
})
