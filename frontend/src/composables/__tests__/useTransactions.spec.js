import { describe, it, expect, vi } from 'vitest'
import { nextTick } from 'vue'
import { useTransactions } from '../useTransactions.js'

vi.mock('@/api/transactions', () => ({
  fetchTransactions: vi.fn(),
}))

// Ensure filteredTransactions pads results to the requested page size
// even when search narrows down matches.
describe('useTransactions', () => {
  it('filters results without padding when searching', () => {
    const { transactions, searchQuery, filteredTransactions } = useTransactions(3)
    transactions.value = [
      { transaction_id: '1', description: 'Coffee', category: 'Food' },
      { transaction_id: '2', description: 'Rent', category: 'Housing' },
      { transaction_id: '3', description: 'Gas', category: 'Transport' },
    ]
    searchQuery.value = 'coffee'
    const result = filteredTransactions.value
    expect(result).toHaveLength(1)

    expect(result.filter((t) => t._placeholder).length).toBe(0)
  })

  it('exposes loading state', async () => {
    const api = await import('@/api/transactions')
    api.fetchTransactions.mockResolvedValue({ transactions: [], total: 0 })
    const { isLoading, fetchTransactions } = useTransactions()
    const promise = fetchTransactions()
    expect(isLoading.value).toBe(true)
    await promise
    expect(isLoading.value).toBe(false)
  })

  it('captures error on failure', async () => {
    const api = await import('@/api/transactions')
    api.fetchTransactions.mockRejectedValue(new Error('fail'))
    const { error, fetchTransactions, isLoading } = useTransactions()
    await fetchTransactions()
    expect(error.value).toBeInstanceOf(Error)
    expect(isLoading.value).toBe(false)
  })
})
