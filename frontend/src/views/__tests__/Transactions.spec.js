// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import Transactions from '../Transactions.vue'

vi.mock('@/api/transactions', () => ({
  fetchTransactions: vi.fn().mockResolvedValue({ transactions: [], total: 0 })
}))

describe('Transactions.vue', () => {
  it('matches snapshot', () => {
    const wrapper = shallowMount(Transactions, {
      global: {
        stubs: ['ImportFileSelector', 'UpdateTransactionsTable', 'RecurringTransactionSection', 'Button', 'Card', 'CreditCard']
      }
    })
    expect(wrapper.html()).toMatchSnapshot()
  })
})
