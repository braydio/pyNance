/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { useTransactions } from './useTransactions.js'
import { fetchTransactions } from '@/api/transactions'

vi.mock('@/api/transactions', () => ({
  fetchTransactions: vi.fn(),
}))

describe('useTransactions', () => {
  const mainPageTransactions = Array.from({ length: 10 }, (_, idx) => ({
    transaction_id: `tx-${idx + 1}`,
    date: '2024-01-01',
    description: `Row ${idx + 1}`,
  }))

  const targetTransaction = {
    transaction_id: 'tx-highlight',
    date: '2024-01-02',
    description: 'Highlighted row',
  }

  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(fetchTransactions).mockImplementation((params) => {
      if (params.transaction_id) {
        return Promise.resolve({ transactions: [targetTransaction], total: 1 })
      }

      return Promise.resolve({ transactions: mainPageTransactions, total: 100 })
    })
  })

  it('loads a targeted transaction without expanding the page size', async () => {
    const targetTransactionIdRef = ref('tx-highlight')
    let composable

    mount({
      template: '<div />',
      setup() {
        composable = useTransactions(10, ref(''), ref({}), { targetTransactionIdRef })
        return {}
      },
    })

    await flushPromises()

    const calls = vi.mocked(fetchTransactions).mock.calls
    const pageSizes = calls.map(([params]) => params.page_size)

    expect(pageSizes).toContain(10)
    expect(pageSizes).toContain(1)
    expect(Math.max(...pageSizes)).toBe(10)

    const targetedCall = calls.find(([params]) => params.transaction_id === 'tx-highlight')
    expect(targetedCall?.[0].page_size).toBe(1)

    composable.searchQuery.value = 'tx-highlight'
    await nextTick()

    const highlighted = composable.filteredTransactions.value.find(
      (tx) => tx.transaction_id === 'tx-highlight',
    )
    expect(highlighted).toBeTruthy()
  })

  it('paginates filtered data and preserves filters across page changes', async () => {
    const filtersRef = ref({ account_ids: ['acct-1'], tx_type: 'debit' })
    const pageSize = 2
    const firstPage = [
      { transaction_id: 'p1-a', date: '2024-02-01', description: 'First' },
      { transaction_id: 'p1-b', date: '2024-01-31', description: 'Second' },
    ]
    const secondPage = [
      { transaction_id: 'p2-a', date: '2024-01-30', description: 'Third' },
      { transaction_id: 'p2-b', date: '2024-01-29', description: 'Fourth' },
    ]

    vi.mocked(fetchTransactions).mockImplementation(({ page, account_ids, tx_type }) => {
      expect(account_ids).toEqual(['acct-1'])
      expect(tx_type).toBe('debit')
      if (page === 2) {
        return Promise.resolve({ transactions: secondPage, total: 4 })
      }
      return Promise.resolve({ transactions: firstPage, total: 4 })
    })

    let composable
    mount({
      template: '<div />',
      setup() {
        composable = useTransactions(pageSize, null, filtersRef)
        return {}
      },
    })
    const {
      fetchTransactions: fetchTransactionsPage,
      paginatedTransactions,
      setPage,
      totalPages,
      totalCount,
    } = composable

    await fetchTransactionsPage(1, { force: true })
    const firstPageIds = paginatedTransactions.value
      .filter((tx) => !tx._placeholder)
      .map((tx) => tx.transaction_id)
    expect(firstPageIds).toEqual(firstPage.map((tx) => tx.transaction_id))
    expect(totalCount.value).toBe(4)
    expect(totalPages.value).toBe(2)

    setPage(2)
    await flushPromises()

    const secondPageIds = paginatedTransactions.value
      .filter((tx) => !tx._placeholder)
      .map((tx) => tx.transaction_id)
    expect(secondPageIds).toEqual(secondPage.map((tx) => tx.transaction_id))
    expect(totalCount.value).toBe(4)
    expect(totalPages.value).toBe(2)
  })
})
