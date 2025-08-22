// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import Transactions from '../Transactions.vue'

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
