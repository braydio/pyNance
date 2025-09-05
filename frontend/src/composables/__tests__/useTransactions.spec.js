import { describe, it, expect } from 'vitest'
import { useTransactions } from '../useTransactions.js'

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
  })
})
