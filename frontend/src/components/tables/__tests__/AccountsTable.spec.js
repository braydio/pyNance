// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import AccountsTable from '../AccountsTable.vue'
import api from '@/services/api'

vi.mock('@/services/api', () => ({
  default: { getAccounts: vi.fn(), setAccountHidden: vi.fn() },
}))
vi.mock('@/api/accounts_link', () => ({ default: { deleteAccount: vi.fn() } }))
vi.mock('vue-toastification', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

const accounts = [
  {
    account_id: 'a',
    name: 'Checking',
    institution_name: 'Bank',
    type: 'depository',
    balance: 10,
    last_refreshed: '2026-10-01',
  },
  {
    account_id: 'b',
    name: 'Card',
    institution_name: 'Bank',
    type: 'credit',
    balance: -5,
    last_refreshed: '2026-10-02',
  },
  {
    account_id: 'c',
    name: 'Old',
    institution_name: 'Bank',
    type: 'depository',
    balance: 1,
    is_hidden: true,
  },
]

const stubs = { AccountSparkline: true, Modal: true }

async function mountTable() {
  api.getAccounts.mockResolvedValue({ status: 'success', accounts })
  const wrapper = mount(AccountsTable, { global: { stubs } })
  await flushPromises()
  return wrapper
}

describe('AccountsTable', () => {
  beforeEach(() => api.getAccounts.mockReset())

  it('filters types with a keyboard-usable checkbox list and removable chips', async () => {
    const wrapper = await mountTable()
    await wrapper.get('[data-testid="toggle-type-filter"]').trigger('click')
    expect(wrapper.get('[data-testid="toggle-type-filter"]').attributes('aria-expanded')).toBe(
      'true',
    )
    const boxes = wrapper.findAll('#account-type-filter input[type="checkbox"]')
    expect(boxes).toHaveLength(2)
    expect(wrapper.find('select[multiple]').exists()).toBe(false)

    await boxes[1].setValue(true) // credit
    expect(wrapper.findAll('tbody tr')).toHaveLength(1)
    expect(wrapper.get('[data-testid="accounts-filter-tags"]').text()).toContain('Credit')

    await wrapper.get('[data-testid="clear-type-filter"]').trigger('click')
    expect(wrapper.findAll('tbody tr')).toHaveLength(2) // hidden account stays hidden by default
  })

  it('keeps hide/delete inside management mode and re-locks delete when leaving it', async () => {
    const wrapper = await mountTable()
    expect(wrapper.find('[data-testid="toggle-delete"]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Delete')

    await wrapper.get('[data-testid="toggle-manage"]').trigger('click')
    expect(wrapper.findAll('tbody button').some((b) => b.text() === 'Hide')).toBe(true)
    expect(wrapper.findAll('tbody button').some((b) => b.text() === 'Delete')).toBe(false)

    await wrapper.get('[data-testid="toggle-delete"]').trigger('click')
    expect(wrapper.findAll('tbody button').some((b) => b.text() === 'Delete')).toBe(true)

    await wrapper.get('[data-testid="toggle-manage"]').trigger('click') // leave management
    await wrapper.get('[data-testid="toggle-manage"]').trigger('click') // re-enter
    expect(wrapper.findAll('tbody button').some((b) => b.text() === 'Delete')).toBe(false)
  })

  it('sorts from header buttons with aria-sort', async () => {
    const wrapper = await mountTable()
    const header = () => wrapper.findAll('thead th').find((th) => th.text().startsWith('Balance'))
    expect(header().attributes('aria-sort')).toBe('none')
    await wrapper.get('[data-testid="sort-balance"]').trigger('click')
    expect(header().attributes('aria-sort')).toBe('ascending')
    await wrapper.get('[data-testid="sort-balance"]').trigger('click')
    expect(header().attributes('aria-sort')).toBe('descending')
  })

  it('shows hidden accounts only when included and reports pressed state', async () => {
    const wrapper = await mountTable()
    const toggle = wrapper.get('[data-testid="toggle-hidden"]')
    expect(toggle.attributes('aria-pressed')).toBe('false')
    await toggle.trigger('click')
    expect(toggle.attributes('aria-pressed')).toBe('true')
    expect(wrapper.findAll('tbody tr')).toHaveLength(3)
  })

  it('shows a retryable error when accounts fail to load', async () => {
    api.getAccounts.mockRejectedValueOnce(new Error('offline'))
    const wrapper = mount(AccountsTable, { global: { stubs } })
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('offline')
    api.getAccounts.mockResolvedValueOnce({ status: 'success', accounts })
    await wrapper.get('[role="alert"] button').trigger('click')
    await flushPromises()
    expect(wrapper.findAll('tbody tr')).toHaveLength(2)
  })
})
