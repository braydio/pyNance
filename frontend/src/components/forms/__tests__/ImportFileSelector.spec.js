// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import axios from 'axios'
import ImportFileSelector from '../ImportFileSelector.vue'

vi.mock('axios', () => ({ default: { get: vi.fn(), post: vi.fn() } }))

describe('ImportFileSelector', () => {
  beforeEach(() => {
    axios.get.mockReset()
    axios.post.mockReset()
    axios.get.mockResolvedValue({ data: ['plaid_transactions_2025-01.csv'] })
  })

  it('labels the file select, uses a plain heading and a non-submitting import button', async () => {
    const wrapper = mount(ImportFileSelector)
    await flushPromises()
    const label = wrapper.get('label[for="import-file-select"]')
    expect(label.text()).toBe('Import file')
    expect(wrapper.get('#import-file-select').exists()).toBe(true)
    const button = wrapper.get('button')
    expect(button.attributes('type')).toBe('button')
    expect(button.text()).toBe('Import selected file')
    expect(button.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).not.toMatch(/Click Me|Go ahead/)
  })

  it('reports success and failure inline instead of alert()', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    axios.post.mockResolvedValueOnce({})
    const wrapper = mount(ImportFileSelector)
    await flushPromises()
    await wrapper.get('#import-file-select').setValue('plaid_transactions_2025-01.csv')
    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(wrapper.get('[role="status"]').text()).toContain('Import started')

    axios.post.mockRejectedValueOnce(new Error('bad'))
    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Failed to import')
    expect(alertSpy).not.toHaveBeenCalled()
  })
})
