// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import TransactionModal from '../TransactionModal.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

describe('TransactionModal.vue', () => {
  it('shows the date column for date drill-downs when requested', () => {
    const wrapper = shallowMount(TransactionModal, {
      props: {
        show: true,
        kind: 'date',
        showDateColumn: true,
        transactions: [{ transaction_id: 'tx-1', date: '2026-07-16', amount: -10 }],
      },
      global: {
        stubs: {
          transition: false,
          ModalTransactionsDisplay: {
            name: 'ModalTransactionsDisplay',
            props: ['showDateColumn'],
            template: '<div class="transactions-display" />',
          },
        },
      },
    })

    expect(wrapper.getComponent({ name: 'ModalTransactionsDisplay' }).props('showDateColumn')).toBe(
      true,
    )
  })
})
