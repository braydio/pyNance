// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import AccountSparkline from '../AccountSparkline.vue'

let balanceHistoryRef
let transactionHistoryRef
let useAccountHistoryMock
let useAccountTransactionHistoryMock

vi.mock('@/composables/useAccountHistory', () => ({
  useAccountHistory: (...args) => useAccountHistoryMock(...args),
}))

vi.mock('@/composables/useAccountTransactionHistory', () => ({
  useAccountTransactionHistory: (...args) => useAccountTransactionHistoryMock(...args),
}))

describe('AccountSparkline', () => {
  beforeEach(() => {
    balanceHistoryRef = ref([
      { date: '2024-01-01', balance: 100 },
      { date: '2024-01-02', balance: 120 },
      { date: '2024-01-03', balance: 110 },
    ])
    transactionHistoryRef = ref([
      { date: '2024-01-01', net_amount: -30, transaction_count: 2 },
      { date: '2024-01-02', net_amount: 15, transaction_count: 1 },
      { date: '2024-01-03', net_amount: 45, transaction_count: 3 },
    ])

    useAccountHistoryMock = vi.fn(() => ({ history: balanceHistoryRef }))
    useAccountTransactionHistoryMock = vi.fn(() => ({
      history: transactionHistoryRef,
    }))
  })

  it('renders points for balance and transaction data', async () => {
    const wrapper = mount(AccountSparkline, {
      props: { accountId: 'acct-123' },
    })

    const balancePoints = wrapper.get('polyline').attributes('points')
    expect(balancePoints).toBeTruthy()

    await wrapper.get('.sparkline-container').trigger('click')
    await nextTick()

    const transactionPoints = wrapper.get('polyline').attributes('points')
    expect(transactionPoints).toBeTruthy()
    expect(transactionPoints).not.toEqual(balancePoints)
  })
})
