import { describe, it, expect, vi, afterEach } from 'vitest'
import { ref } from 'vue'
import { useTransactions } from '../useTransactions.js'
import { fetchTransactions as fetchTransactionsApi } from '@/api/transactions'

vi.mock('@/api/transactions', () => ({
  fetchTransactions: vi.fn(),
}))

afterEach(() => {
  vi.clearAllMocks()
})

describe('useTransactions', () => {
  it('does not narrow loaded rows locally: search is a server filter', () => {
    const { transactions, searchQuery, filteredTransactions } = useTransactions(3)
    transactions.value = [
      { transaction_id: '1', description: 'Coffee', category: 'Food' },
      { transaction_id: '2', description: 'Rent', category: 'Housing' },
      { transaction_id: '3', description: 'Gas', category: 'Transport' },
    ]
    searchQuery.value = 'coffee'
    // The loaded rows are untouched; the matching rows arrive from the API with `search`.
    expect(filteredTransactions.value).toHaveLength(3)
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

  it('requests running balances only when explicitly enabled', async () => {
    fetchTransactionsApi.mockResolvedValue({ transactions: [], total: 0 })
    const filters = ref({ account_ids: ['acc-1'] })

    const { fetchTransactions } = useTransactions(5, null, filters, {
      includeRunningBalance: true,
    })

    await fetchTransactions(1, { force: true })

    expect(fetchTransactionsApi).toHaveBeenCalledWith(
      expect.objectContaining({ include_running_balance: true, account_ids: ['acc-1'] }),
    )
  })
})
