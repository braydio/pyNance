// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import Transactions from '../Transactions.vue'

vi.mock('@/api/transactions', () => ({
  fetchTransactions: vi.fn().mockResolvedValue({ transactions: [], total: 0 }),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
}))

describe('Transactions.vue', () => {
  it('matches snapshot', () => {
    const wrapper = shallowMount(Transactions, {
      global: {
        stubs: [
          'AccountActionsSidebar',
          'UpdateTransactionsTable',
          'RecurringTransactionSection',
          'InternalTransferScanner',
          'UiButton',
          'Card',
          'CreditCard',
          'TabbedPageLayout',
        ],
      },
    })
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('defaults to Activity tab', () => {
    const wrapper = shallowMount(Transactions, {
      global: {
        stubs: [
          'AccountActionsSidebar',
          'UpdateTransactionsTable',
          'RecurringTransactionSection',
          'InternalTransferScanner',
          'UiButton',
          'Card',
          'CreditCard',
          'TabbedPageLayout',
        ],
      },
    })

    expect(wrapper.vm.activeTab).toBe('Activity')
    wrapper.vm.activeTab = 'Scanner'
    expect(wrapper.vm.activeTab).toBe('Scanner')
  })
})
