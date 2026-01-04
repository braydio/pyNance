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

  it('backfills filtered results across cached pages before paginating', async () => {
    const filtersRef = ref({ account_ids: ['acct-1'] })
    const pageSize = 2
    const firstPage = [
      { transaction_id: 'alpha-1', date: '2024-02-01', description: 'Apple Store' },
      { transaction_id: 'beta-1', date: '2024-02-02', description: 'Book Shop' },
    ]
    const secondPage = [
      { transaction_id: 'alpha-2', date: '2024-02-03', description: 'Apricot Market' },
      { transaction_id: 'gamma-1', date: '2024-02-04', description: 'Grocery' },
    ]

    vi.mocked(fetchTransactions).mockImplementation(({ page, account_ids }) => {
      expect(account_ids).toEqual(['acct-1'])
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
      searchQuery,
      totalCount,
    } = composable

    await fetchTransactionsPage(1, { force: true })
    await fetchTransactionsPage(2, { force: true })
    await flushPromises()

    searchQuery.value = 'ap'
    await nextTick()

    const filteredIds = paginatedTransactions.value.map((tx) => tx.transaction_id)
    expect(filteredIds).toEqual(expect.arrayContaining(['alpha-1', 'alpha-2']))
    expect(filteredIds).toHaveLength(2)
    expect(totalCount.value).toBe(2)
  })

  it('fills the visible page when filtered API responses are sparse', async () => {
    const filtersRef = ref({ account_ids: ['acct-1'] })
    const pageSize = 2
    const firstPage = [{ transaction_id: 'only-1', date: '2024-02-01', description: 'Solo' }]
    const secondPage = [
      { transaction_id: 'only-2', date: '2024-02-02', description: 'Second' },
      { transaction_id: 'only-3', date: '2024-02-03', description: 'Third' },
    ]

    vi.mocked(fetchTransactions).mockImplementation(({ page, account_ids }) => {
      expect(account_ids).toEqual(['acct-1'])
      if (page === 1) {
        return Promise.resolve({ transactions: firstPage, total: 3 })
      }
      return Promise.resolve({ transactions: secondPage, total: 3 })
    })

    let composable
    mount({
      template: '<div />',
      setup() {
        composable = useTransactions(pageSize, null, filtersRef)
        return {}
      },
    })

    const { fetchTransactions: fetchTransactionsPage, paginatedTransactions, totalCount } =
      composable

    await fetchTransactionsPage(1, { force: true })
    await flushPromises()

    const pageIds = paginatedTransactions.value.map((tx) => tx.transaction_id)
    expect(pageIds).toEqual(['only-3', 'only-2'])
    expect(totalCount.value).toBe(3)
  })
})
