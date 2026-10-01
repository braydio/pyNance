// @vitest-environment jsdom
import { beforeEach, describe, it, expect, vi } from 'vitest'
import { flushPromises, shallowMount } from '@vue/test-utils'
import SettingsView from '../Settings.vue'

const { getLlmSettings, updateLlmSettings } = vi.hoisted(() => ({
  getLlmSettings: vi.fn(),
  updateLlmSettings: vi.fn(),
}))

vi.mock('@/services/api', () => ({
  default: { getLlmSettings, updateLlmSettings },
}))

describe('Settings.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getLlmSettings.mockResolvedValue({
      data: { custom_message_enabled: true, base_url: 'http://localhost:11434' },
    })
    updateLlmSettings.mockResolvedValue({
      data: { custom_message_enabled: false, base_url: 'http://localhost:11434' },
    })
  })

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

  it('loads and saves dashboard LLM settings', async () => {
    const wrapper = shallowMount(SettingsView, {
      global: {
        stubs: {
          BasePageLayout: { template: '<div><slot /></div>' },
          PageHeader: { template: '<div />' },
          BaseInput: {
            props: ['modelValue'],
            template:
              '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
          },
          BaseButton: { template: '<button @click="$emit(\'click\')"><slot /></button>' },
          RefreshPlaidControls: true,
        },
      },
    })
    await flushPromises()

    expect(getLlmSettings).toHaveBeenCalledOnce()
    await wrapper.get('[data-testid="llm-message-toggle"]').setValue(false)
    await wrapper.get('[data-testid="llm-settings-save"]').trigger('click')
    await flushPromises()

    expect(updateLlmSettings).toHaveBeenCalledWith({
      custom_message_enabled: false,
      base_url: 'http://localhost:11434',
    })
    expect(wrapper.get('[data-testid="llm-settings-feedback"]').text()).toContain('saved')
  })
})
