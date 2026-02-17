// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import Accounts from '../Accounts.vue'
import { vi } from 'vitest'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {} }),
  useRouter: () => ({ push: vi.fn() }),
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
  rangeToDates: vi.fn().mockReturnValue({ start: '2025-01-01', end: '2025-01-31' }),
}))

vi.mock('@/stores/useAccountPreferences', () => ({
  useAccountPreferences: () => ({
    getSelectedRange: vi.fn().mockReturnValue('30d'),
    setSelectedRange: vi.fn(),
  }),
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
})
