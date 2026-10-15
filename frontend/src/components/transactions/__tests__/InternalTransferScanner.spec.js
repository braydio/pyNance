// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import InternalTransferScanner from '../InternalTransferScanner.vue'
import api from '@/services/api.js'

vi.mock('@/services/api.js', () => ({
  default: { scanInternalTransfers: vi.fn(), updateTransaction: vi.fn() },
}))

const pair = {
  transaction_id: 't1',
  counterpart_id: 't2',
  amount: -50,
  description: 'Transfer out',
  account_name: 'Checking',
  institution_name: 'Bank',
  match_score: 0.9,
  time_delta_hours: 2,
  counterpart: {
    amount: 50,
    description: 'Transfer in',
    account_name: 'Savings',
    institution_name: 'Bank',
  },
}

describe('InternalTransferScanner', () => {
  it('uses themed muted text and non-submitting buttons', async () => {
    api.scanInternalTransfers.mockResolvedValue({ pairs: [pair] })
    const wrapper = mount(InternalTransferScanner)
    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(wrapper.html()).not.toContain('text-gray-500')
    expect(wrapper.html()).toContain('text-muted')
    wrapper.findAll('button').forEach((b) => expect(b.attributes('type')).toBe('button'))
  })

  it('shows an error when scanning fails instead of claiming there are no transfers', async () => {
    api.scanInternalTransfers.mockRejectedValueOnce(new Error('down'))
    const wrapper = mount(InternalTransferScanner)
    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Unable to scan')
    expect(wrapper.text()).not.toContain('No internal transfers found')
  })
})
