import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { useAccountTransactionHistory } from '../useAccountTransactionHistory.js'

let fetchAccountTransactionHistory

vi.mock('@/api/accounts', () => ({
  fetchAccountTransactionHistory: (...args) => fetchAccountTransactionHistory(...args),
}))

describe('useAccountTransactionHistory', () => {
  beforeEach(() => {
    fetchAccountTransactionHistory = vi.fn()
  })

  it('normalizes the payload into daily net amounts', async () => {
    fetchAccountTransactionHistory.mockResolvedValue({
      status: 'success',
      transactions: [
        { date: '2024-03-02', amount: 20 },
        { date: '2024-03-01', amount: -10 },
        { date: '2024-03-01', amount: 5 },
      ],
    })

    const { history, loading } = useAccountTransactionHistory('acct-1')

    await flushPromises()

    expect(fetchAccountTransactionHistory).toHaveBeenCalledWith('acct-1')
    expect(loading.value).toBe(false)
    expect(history.value).toEqual([
      { date: '2024-03-01', net_amount: -5, transaction_count: 2 },
      { date: '2024-03-02', net_amount: 20, transaction_count: 1 },
    ])
  })
})
