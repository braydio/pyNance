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
          'ImportFileSelector',
          'UpdateTransactionsTable',
          'RecurringTransactionSection',
          'Button',
          'Card',
          'CreditCard',
          'BasePageLayout',
        ],
      },
    })
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('toggles control visibility', async () => {
    const wrapper = shallowMount(Transactions, {
      global: {
        stubs: [
          'ImportFileSelector',
          'UpdateTransactionsTable',
          'RecurringTransactionSection',
          'Button',
          'Card',
          'CreditCard',
          'BasePageLayout',
        ],
      },
    })

    expect(wrapper.vm.showControls).toBe(false)
    wrapper.vm.toggleControls()
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.showControls).toBe(true)
  })
})
