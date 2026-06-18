// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import axios from 'axios'
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
    get: vi.fn(),
    post: vi.fn(),
  },
}))

/** Mount Settings with only route-level layout dependencies stubbed. */
const mountSettings = () =>
  mount(SettingsView, {
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

/** Create a controllable promise for asserting in-flight request behavior. */
const deferred = () => {
  let resolve
  let reject
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

describe('Settings.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    axios.get.mockResolvedValue({ data: { themes: ['dark'], current_theme: 'dark' } })
  })

  it('keeps Appearance and Connected Accounts sections intact', async () => {
    const wrapper = mountSettings()

    await flushPromises()

    expect(wrapper.text()).toContain('Appearance')
    expect(wrapper.text()).toContain('Connected Accounts')
    expect(wrapper.find('refresh-plaid-controls-stub').exists()).toBe(true)
  })

  it('disables command execution until required fields are valid', async () => {
    const wrapper = mountSettings()
    const submit = wrapper.get('[data-testid="command-submit"]')

    expect(submit.attributes('disabled')).toBeDefined()

    await wrapper.get('#command-argument').setValue('   ')
    expect(submit.attributes('disabled')).toBeDefined()

    await wrapper.get('#command-argument').setValue('refresh checking balances')
    expect(submit.attributes('disabled')).toBeUndefined()
  })

  it('sends the backend command payload and renders successful output', async () => {
    axios.post.mockResolvedValueOnce({
      data: { status: 'success', stdout: 'balances refreshed', stderr: '' },
    })
    const wrapper = mountSettings()

    await wrapper.get('#command-template').setValue('sync-transactions')
    await wrapper.get('#command-argument').setValue('  sync account 123  ')
    await wrapper.get('[data-testid="command-submit"]').trigger('click')
    await flushPromises()

    expect(axios.post).toHaveBeenCalledWith('/api/codex/exec', {
      preset: 'sync-transactions',
      task: 'sync account 123',
    })
    expect(wrapper.get('[data-testid="command-feedback"]').text()).toBe(
      'Command completed successfully.',
    )
    expect(wrapper.get('[data-testid="command-output"]').text()).toBe('balances refreshed')
  })

  it('toggles loading state and prevents duplicate command submissions', async () => {
    const request = deferred()
    axios.post.mockReturnValueOnce(request.promise)
    const wrapper = mountSettings()

    await wrapper.get('#command-argument').setValue('refresh account balances')
    const submit = wrapper.get('[data-testid="command-submit"]')
    await submit.trigger('click')

    expect(submit.attributes('disabled')).toBeDefined()
    expect(submit.text()).toBe('Running command…')

    await submit.trigger('click')
    expect(axios.post).toHaveBeenCalledTimes(1)

    request.resolve({ data: { status: 'success', stdout: '', stderr: '' } })
    await flushPromises()

    expect(submit.attributes('disabled')).toBeUndefined()
    expect(submit.text()).toBe('Run command')
  })

  it('renders backend validation feedback', async () => {
    axios.post.mockRejectedValueOnce({
      response: {
        status: 400,
        data: { status: 'error', error: 'task contains disallowed characters' },
      },
    })
    const wrapper = mountSettings()

    await wrapper.get('#command-argument').setValue('invalid task')
    await wrapper.get('[data-testid="command-submit"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-testid="command-feedback"]').text()).toBe(
      'task contains disallowed characters',
    )
  })

  it('renders timeout feedback and allows the user to retry', async () => {
    axios.post.mockRejectedValueOnce({
      response: { status: 504, data: { status: 'error', error: 'command timed out' } },
    })
    const wrapper = mountSettings()

    await wrapper.get('#command-argument').setValue('slow account refresh')
    await wrapper.get('[data-testid="command-submit"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-testid="command-feedback"]').text()).toBe('command timed out')
    expect(wrapper.get('[data-testid="command-submit"]').attributes('disabled')).toBeUndefined()
  })
})
