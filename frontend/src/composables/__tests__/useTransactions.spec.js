import { describe, it, expect, vi, afterEach } from 'vitest'
import { useTransactions } from '../useTransactions.js'
import { fetchTransactions as fetchTransactionsApi } from '@/api/transactions'

vi.mock('@/api/transactions', () => ({
  fetchTransactions: vi.fn(),
}))

afterEach(() => {
  vi.clearAllMocks()
})

// Ensure filteredTransactions returns only search matches without padding
// when a query is applied.
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
  })

  it('keeps API category when no primary/detailed fields are provided', async () => {
    fetchTransactionsApi.mockResolvedValue({
      transactions: [{ transaction_id: '1', description: 'Coffee', category: 'Food & Drink' }],
      total: 1,
    })
    const { fetchTransactions, transactions } = useTransactions(5)

    await fetchTransactions(1, { force: true })

    expect(transactions.value[0].category).toBe('Food & Drink')
  })
})
