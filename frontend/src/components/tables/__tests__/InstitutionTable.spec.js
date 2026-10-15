// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import InstitutionTable from '../InstitutionTable.vue'
import api from '@/services/api'

vi.mock('@/services/api', () => ({
  default: { getInstitutions: vi.fn(), refreshInstitution: vi.fn() },
}))

const institutions = [
  {
    id: 1,
    name: 'First Bank',
    provider: 'plaid',
    last_refreshed: '2026-10-01T12:00:00Z',
    accounts: [
      { account_id: 'a', name: 'Checking', type: 'depository', balance: 12.5, link_type: 'plaid' },
    ],
  },
]

describe('InstitutionTable', () => {
  beforeEach(() => {
    api.getInstitutions.mockReset()
    api.refreshInstitution.mockReset()
    api.getInstitutions.mockResolvedValue({ status: 'success', institutions })
  })

  it('expands from a real button with aria-expanded/aria-controls, not a clickable row', async () => {
    const wrapper = mount(InstitutionTable)
    await flushPromises()
    const toggle = wrapper.get('[data-testid="institution-toggle-1"]')
    expect(toggle.element.tagName).toBe('BUTTON')
    expect(toggle.attributes('type')).toBe('button')
    expect(toggle.attributes('aria-expanded')).toBe('false')
    expect(wrapper.find('tbody tr.cursor-pointer').exists()).toBe(false)

    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('true')
    const panel = wrapper.get(`#${toggle.attributes('aria-controls')}`)
    expect(panel.classes()).toContain('nested-scroll')
    expect(panel.text()).toContain('Checking')
    expect(panel.text()).toContain('$12.50')
  })

  it('shows refresh progress and a per-institution error without toggling the row', async () => {
    let reject
    api.refreshInstitution.mockImplementationOnce(() => new Promise((_, r) => (reject = r)))
    const wrapper = mount(InstitutionTable)
    await flushPromises()
    const refresh = wrapper.get('[data-testid="institution-refresh-1"]')
    await refresh.trigger('click')
    expect(refresh.text()).toBe('Refreshing…')
    expect(refresh.attributes('disabled')).toBeDefined()
    expect(wrapper.get('[data-testid="institution-toggle-1"]').attributes('aria-expanded')).toBe(
      'false',
    )

    reject(new Error('rate limited'))
    await flushPromises()
    expect(wrapper.get('[data-testid="institution-refresh-error-1"]').text()).toContain(
      'rate limited',
    )
    expect(wrapper.get('[data-testid="institution-refresh-1"]').text()).toBe('Refresh')
  })

  it('shows a retryable error when institutions fail to load', async () => {
    api.getInstitutions.mockRejectedValueOnce(new Error('down'))
    const wrapper = mount(InstitutionTable)
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Unable to load institutions')
    await wrapper.get('[role="alert"] button').trigger('click')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('First Bank')
  })
})
