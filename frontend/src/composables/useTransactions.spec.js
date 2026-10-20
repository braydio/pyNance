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

  it('searches on the server across all matching rows and trusts the server total', async () => {
    vi.useFakeTimers()
    try {
      const filtersRef = ref({ account_ids: ['acct-1'] })
      vi.mocked(fetchTransactions).mockImplementation(({ search }) =>
        Promise.resolve(
          search
            ? { transactions: [{ transaction_id: 'alpha-9', date: '2024-02-01' }], total: 51 }
            : { transactions: [{ transaction_id: 'beta-1', date: '2024-02-02' }], total: 400 },
        ),
      )
      let composable
      mount({
        template: '<div />',
        setup() {
          composable = useTransactions(15, null, filtersRef)
          return {}
        },
      })
      await flushPromises()
      expect(composable.totalCount.value).toBe(400)

      composable.searchQuery.value = 'ap'
      await nextTick()
      // Debounced: typing does not fire a request per keystroke.
      expect(vi.mocked(fetchTransactions).mock.calls.some(([p]) => p.search)).toBe(false)

      await vi.advanceTimersByTimeAsync(350)
      await flushPromises()

      expect(fetchTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'ap', account_ids: ['acct-1'], page: 1 }),
      )
      expect(composable.queryFilters.value).toMatchObject({ search: 'ap' })
      // The count is the server's whole-set count, not the number of loaded rows.
      expect(composable.totalCount.value).toBe(51)
      expect(composable.totalPages.value).toBe(4)
      expect(composable.currentPageRows.value.map((tx) => tx.transaction_id)).toEqual(['alpha-9'])

      composable.searchQuery.value = ''
      await flushPromises()
      expect(composable.queryFilters.value.search).toBeUndefined()
      expect(composable.totalCount.value).toBe(400)
    } finally {
      vi.useRealTimers()
    }
  })

  it('keeps each server page separate so a jump to page 5 does not need pages 2-4', async () => {
    const filtersRef = ref({})
    vi.mocked(fetchTransactions).mockImplementation(({ page }) =>
      Promise.resolve({
        transactions: [{ transaction_id: `p${page}-a`, date: '2024-02-01' }],
        total: 100,
      }),
    )
    let composable
    mount({
      template: '<div />',
      setup() {
        composable = useTransactions(10, null, filtersRef)
        return {}
      },
    })
    await flushPromises()
    composable.setPage(5)
    await flushPromises()
    expect(composable.currentPageRows.value.map((tx) => tx.transaction_id)).toEqual(['p5-a'])
  })

  it('ignores a slow response for filters that were replaced', async () => {
    const filtersRef = ref({ tx_type: 'debit' })
    let releaseFirst
    vi.mocked(fetchTransactions).mockImplementation(({ tx_type }) => {
      if (tx_type === 'debit') {
        return new Promise((resolve) => {
          releaseFirst = () =>
            resolve({ transactions: [{ transaction_id: 'old', date: '2024-01-01' }], total: 9 })
        })
      }
      return Promise.resolve({
        transactions: [{ transaction_id: 'new', date: '2024-01-02' }],
        total: 1,
      })
    })
    let composable
    mount({
      template: '<div />',
      setup() {
        composable = useTransactions(10, null, filtersRef)
        return {}
      },
    })
    await nextTick()
    filtersRef.value = { tx_type: 'credit' }
    await flushPromises()
    releaseFirst()
    await flushPromises()

    expect(composable.currentPageRows.value.map((tx) => tx.transaction_id)).toEqual(['new'])
    expect(composable.totalCount.value).toBe(1)
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

    const {
      fetchTransactions: fetchTransactionsPage,
      paginatedTransactions,
      totalCount,
    } = composable

    await fetchTransactionsPage(1, { force: true })
    await flushPromises()

    const pageIds = paginatedTransactions.value.map((tx) => tx.transaction_id)
    expect(pageIds).toEqual(['only-3', 'only-2'])
    expect(totalCount.value).toBe(3)
  })
})
