// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import Accounts from '../Accounts.vue'
import { vi } from 'vitest'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {} }),
  useRouter: () => ({}),
}))

vi.mock('@/api/accounts', () => ({
  fetchNetChanges: vi
    .fn()
    .mockResolvedValue({ status: 'success', data: { income: 0, expense: 0, net: 0 } }),
  fetchRecentTransactions: vi.fn().mockResolvedValue({ data: { transactions: [] } }),
}))

describe('Accounts.vue', () => {
  it('matches snapshot', () => {
    const wrapper = shallowMount(Accounts, {
      global: {
        stubs: ['TabbedPageLayout', 'AccountActionsSidebar'],
      },
    })
    expect(wrapper.html()).toMatchSnapshot()
  })
})
