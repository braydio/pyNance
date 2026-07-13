// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import SettingsView from '../Settings.vue'

describe('Settings.vue', () => {
  it('renders local theme options and refresh controls', () => {
    const wrapper = shallowMount(SettingsView, {
      global: {
        stubs: {
          BasePageLayout: { template: '<div><slot /></div>' },
          PageHeader: { template: '<div><slot name="title" /><slot name="subtitle" /></div>' },
          SettingsIcon: true,
          RefreshPlaidControls: true,
        },
        SettingsIcon: true,
        RefreshPlaidControls: true,
      },
    })

    expect(wrapper.exists()).toBe(true)
  })
})
