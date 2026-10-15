// @vitest-environment jsdom
import { beforeEach, describe, it, expect, vi } from 'vitest'
import { flushPromises, shallowMount } from '@vue/test-utils'
import SettingsView from '../Settings.vue'
import axios from 'axios'

vi.mock('axios', () => ({ default: { post: vi.fn(), get: vi.fn() } }))

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

  it('keeps local command execution in a collapsed Advanced disclosure after normal preferences', () => {
    const wrapper = shallowMount(SettingsView, {
      global: {
        stubs: { RefreshPlaidControls: true, BasePageLayout: { template: '<div><slot /></div>' } },
      },
    })
    const advanced = wrapper.get('[data-testid="advanced-settings"]')
    expect(advanced.element.tagName).toBe('DETAILS')
    expect(advanced.attributes('open')).toBeUndefined()
    expect(advanced.find('[data-testid="command-submit"]').exists()).toBe(true)

    const html = wrapper.html()
    expect(html.indexOf('Connected Accounts')).toBeLessThan(
      html.indexOf('data-testid="advanced-settings"'),
    )
    expect(html.indexOf('Dashboard AI message')).toBeLessThan(
      html.indexOf('data-testid="advanced-settings"'),
    )
  })

  describe('local commands (restored)', () => {
    const mountSettings = () =>
      shallowMount(SettingsView, {
        global: {
          stubs: {
            BasePageLayout: { template: '<div><slot /></div>' },
            PageHeader: { template: '<div />' },
            RefreshPlaidControls: true,
            BaseInput: {
              props: ['modelValue'],
              template:
                '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            },
            BaseSelect: {
              props: ['modelValue'],
              template:
                '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
            },
            BaseButton: {
              inheritAttrs: true,
              template: '<button v-bind="$attrs" @click="$emit(\'click\')"><slot /></button>',
            },
          },
        },
      })

    it('keeps Run disabled until the argument is non-blank', async () => {
      const wrapper = mountSettings()
      const submit = wrapper.get('[data-testid="command-submit"]')
      expect(submit.attributes('disabled')).toBeDefined()
      await wrapper.get('#command-argument').setValue('   ')
      expect(submit.attributes('disabled')).toBeDefined()
      await wrapper.get('#command-argument').setValue('refresh checking balances')
      expect(submit.attributes('disabled')).toBeUndefined()
    })

    it('posts the backend payload and shows success output with a copy action', async () => {
      axios.post.mockResolvedValueOnce({
        data: { status: 'success', stdout: 'balances refreshed' },
      })
      const writeText = vi.fn().mockResolvedValue(undefined)
      Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
      const wrapper = mountSettings()
      await wrapper.get('#command-template').setValue('sync-transactions')
      await wrapper.get('#command-argument').setValue('  sync account 123  ')
      await wrapper.get('[data-testid="command-submit"]').trigger('click')
      await flushPromises()

      expect(axios.post).toHaveBeenCalledWith('/api/codex/exec', {
        preset: 'sync-transactions',
        task: 'sync account 123',
      })
      const feedback = wrapper.get('[data-testid="command-feedback"]')
      expect(feedback.text()).toBe('Command completed successfully.')
      expect(feedback.attributes('role')).toBe('status')
      expect(feedback.attributes('aria-live')).toBe('polite')
      expect(wrapper.get('[data-testid="command-output"]').text()).toBe('balances refreshed')

      await wrapper.get('[data-testid="command-copy"]').trigger('click')
      await flushPromises()
      expect(writeText).toHaveBeenCalledWith('balances refreshed')
      expect(wrapper.get('[data-testid="command-copy"]').text()).toBe('Copied')
    })

    it('prevents duplicate submissions while running and announces errors as alerts', async () => {
      let reject
      axios.post.mockReturnValueOnce(new Promise((_, r) => (reject = r)))
      const wrapper = mountSettings()
      await wrapper.get('#command-argument').setValue('run it')
      const submit = wrapper.get('[data-testid="command-submit"]')
      await submit.trigger('click')
      expect(submit.text()).toBe('Running command…')
      await submit.trigger('click')
      expect(axios.post).toHaveBeenCalledTimes(1)

      reject({ response: { data: { error: 'task contains disallowed characters' } } })
      await flushPromises()
      const feedback = wrapper.get('[data-testid="command-feedback"]')
      expect(feedback.text()).toBe('task contains disallowed characters')
      expect(feedback.attributes('role')).toBe('alert')
      expect(submit.text()).toBe('Run command')
    })
  })

  it('orders Appearance, Connected Accounts, AI settings, then the collapsed Advanced section', () => {
    const wrapper = shallowMount(SettingsView, {
      global: {
        stubs: { RefreshPlaidControls: true, BasePageLayout: { template: '<div><slot /></div>' } },
      },
    })
    const html = wrapper.html()
    const order = [
      'Appearance',
      'Connected Accounts',
      'Dashboard AI message',
      'data-testid="advanced-settings"',
    ].map((marker) => html.indexOf(marker))
    expect(order.every((i) => i >= 0)).toBe(true)
    expect([...order].sort((a, b) => a - b)).toEqual(order)
    expect(wrapper.get('[data-testid="advanced-settings"]').attributes('open')).toBeUndefined()
  })

  it('gives the LLM URL a wider constrained field and describes it with its help text', async () => {
    const wrapper = shallowMount(SettingsView, {
      global: {
        stubs: { RefreshPlaidControls: true, BasePageLayout: { template: '<div><slot /></div>' } },
      },
    })
    await flushPromises()
    const url = wrapper.get('[data-testid="llm-base-url"]')
    expect(url.classes()).toContain('settings-input--wide')
    expect(wrapper.find('#llm-base-url-help').exists()).toBe(true)
  })
})
