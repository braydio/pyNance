// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { vi } from 'vitest'
import Accounts from '../Accounts.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {}, query: {} }),
  useRouter: () => ({}),
}))

vi.mock('vue-toastification', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), info: vi.fn() }),
}))

vi.mock('@/services/api', () => ({
  default: {
    getAccounts: vi.fn().mockResolvedValue({ accounts: [] }),
  },
}))

vi.mock('@/api/accounts', () => ({
  fetchNetChanges: vi
    .fn()
    .mockResolvedValue({ status: 'success', data: { income: 0, expense: 0, net: 0 } }),
  fetchAccountHistory: vi.fn().mockResolvedValue({ balances: [] }),
  fetchRecentTransactions: vi.fn().mockResolvedValue({ transactions: [] }),
  rangeToDates: vi.fn().mockReturnValue({ start: '2024-01-01', end: '2024-01-30' }),
}))

describe('Accounts.vue', () => {
  it('matches snapshot', () => {
    const wrapper = shallowMount(Accounts, {
      global: {
        stubs: ['TabbedPageLayout', 'AccountActionsSidebar', 'LinkedAccountsSection'],
      },
    })
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('passes AccountActionsSidebar into the tab layout sidebar slot', () => {
    const wrapper = shallowMount(Accounts, {
      global: {
        stubs: {
          TabbedPageLayout: {
            template: '<div><slot name="sidebar" /></div>',
          },
          AccountActionsSidebar: true,
          LinkedAccountsSection: true,
        },
      },
    })

    expect(wrapper.find('account-actions-sidebar-stub').exists()).toBe(true)
  })
})
