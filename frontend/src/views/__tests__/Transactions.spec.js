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
  const globalStubs = [
    'ImportFileSelector',
    'UpdateTransactionsTable',
    'RecurringTransactionSection',
    'Button',
    'Card',
    'CreditCard',
    'BasePageLayout',
  ]

  it('matches snapshot', () => {
    const wrapper = shallowMount(Transactions, {
      global: {
        stubs: globalStubs,
      },
    })
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('toggles control visibility', async () => {
    const wrapper = shallowMount(Transactions, {
      global: {
        stubs: globalStubs,
      },
    })

    expect(wrapper.vm.showControls).toBe(false)
    wrapper.vm.toggleControls()
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.showControls).toBe(true)
  })

  // additional tests can be added here
})
