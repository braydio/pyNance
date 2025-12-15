// File: src/composables/useTransactions.js

/**
 * Provides transaction table state and helpers for dashboard components.
 * Handles pagination, search, and sort logic while fetching from the API.
 * Supports dynamic filters via ``filtersRef`` (e.g., ``start_date`` or
 * ``account_ids``) which trigger refetches when changed.
 */
import { ref, computed, onMounted, watch } from 'vue'
import Fuse from 'fuse.js'
import { fetchTransactions as fetchTransactionsApi } from '@/api/transactions'

/**
 * Centralised pagination helper for transaction tables.
 *
 * The composable keeps the currently active page in sync with API responses and
 * deduplicates server calls by caching the most recent response for each page
 * while a filter set is active. When filters change the cache is cleared and
 * the table resets back to page ``1`` so the UI always reflects the newly
 * selected date range, account or transaction type.
 *
 * @param {number} pageSize - Number of rows to request from the API.
 * @param {import('vue').Ref<string | null>} promoteIdRef - Optional transaction
 *   id to prioritise in the client-side sort.
 * @param {import('vue').Ref<Record<string, unknown>>} filtersRef - Reactive
 *   collection of API filter parameters.
 * @param {Object} options - Additional configuration flags.
 * @param {boolean} [options.includeRunningBalance=false] - Request running
 *   balances from the API when the UI needs the column.
 * @param {import('vue').Ref<string | null>} [options.targetTransactionIdRef]
 *   - Optional transaction id to fetch explicitly so it can be highlighted when
 *   it is not on the first page of results.
 */
export function useTransactions(
  pageSize = 15,
  promoteIdRef = null,
  filtersRef = ref({}),
  options = {},
) {
  const transactions = ref([])
  const searchQuery = ref('')
  const sortKey = ref('date')
  const sortOrder = ref(-1)
  const currentPage = ref(1)
  const totalPages = ref(1)
  const totalCount = ref(0)
  const isLoading = ref(false)
  const error = ref(null)

  /** @type {Map<number, Array>} */
  let pageCache = new Map()
  let lastTotal = 0

  /**
   * Fetch a page of transactions from the API.
   *
   * Some backend responses omit the `status` field and return the data
   * object directly. This helper normalizes both shapes so the table renders
   * even when the backend does not include a status key.
   */
  const { includeRunningBalance = false } = options

  const targetTransactionIdRef = options.targetTransactionIdRef || null

  const targetTransactionId = computed(() => {
    if (!targetTransactionIdRef) return ''
    return targetTransactionIdRef.value ? String(targetTransactionIdRef.value) : ''
  })

  /**
   * Retrieve a specific transaction by id without inflating the primary page size.
   *
   * @param {string} transactionId - Identifier to fetch.
   * @returns {Promise<Object|null>} Normalized transaction when available.
   */
  async function fetchTargetTransaction(transactionId) {
    if (!transactionId) return null

    try {
      const res = await fetchTransactionsApi({
        page: 1,
        page_size: 1,
        transaction_id: transactionId,
        ...(includeRunningBalance ? { include_running_balance: true } : {}),
        ...(filtersRef.value || {}),
      })

      if (!res || !Array.isArray(res.transactions) || res.transactions.length === 0) {
        return null
      }

      return {
        ...res.transactions[0],
        category: formatCategory(res.transactions[0]),
      }
    } catch (err) {
      console.warn('Unable to fetch targeted transaction', err)
      return null
    }
  }

  function mergeWithTarget(transactionsForPage, targetTx) {
    if (!targetTx) return transactionsForPage

    const exists = transactionsForPage.some(
      (tx) => String(tx.transaction_id || '') === String(targetTx.transaction_id || ''),
    )
    if (exists) return transactionsForPage

    const merged = [targetTx, ...transactionsForPage]
    return merged.slice(0, pageSize)
  }

  const fetchTransactions = async (page = currentPage.value, { force = false } = {}) => {
    const cached = pageCache.get(page)
    const shouldUseCache = !force && cached

    if (shouldUseCache && !targetTransactionId.value) {
      isLoading.value = false
      error.value = null
      transactions.value = cached
      totalPages.value = Math.max(1, Math.ceil((lastTotal || cached.length) / pageSize))
      return
    }

    isLoading.value = true
    error.value = null
    try {
      const [res, targetTx] = await Promise.all([
        shouldUseCache
          ? Promise.resolve({
              transactions: cached,
              total: lastTotal || cached.length,
            })
          : fetchTransactionsApi({
              page,
              page_size: pageSize,
              ...(includeRunningBalance ? { include_running_balance: true } : {}),
              ...(filtersRef.value || {}),
            }),
        fetchTargetTransaction(targetTransactionId.value),
      ])

      if (!res || typeof res !== 'object' || !('transactions' in res)) {
        console.error('Unexpected response shape:', res)
        error.value = new Error('Received an unexpected response from the server.')
        transactions.value = []
        totalPages.value = 1
        totalCount.value = 0
        pageCache.clear()
        return
      }

      const normalised = (res.transactions || []).map((tx) => ({
        ...tx,
        category: formatCategory(tx),
      }))

      const merged = mergeWithTarget(normalised, targetTx)

      lastTotal = res.total != null ? res.total : normalised.length
      totalCount.value = lastTotal
      totalPages.value = Math.max(1, Math.ceil(lastTotal / pageSize))
      transactions.value = merged
      pageCache.set(page, merged)
    } catch (err) {
      console.error('Error fetching transactions:', err)
      error.value = err
    } finally {
      isLoading.value = false
    }
  }

  const setPage = (page) => {
    const clamped = Math.max(1, Math.min(page, totalPages.value || 1))
    if (clamped !== currentPage.value) {
      currentPage.value = clamped
    } else {
      fetchTransactions(clamped, { force: true })
    }
  }

  const changePage = (delta) => {
    setPage(currentPage.value + delta)
  }

  const setSort = (key) => {
    if (sortKey.value === key) {
      sortOrder.value *= -1
    } else {
      sortKey.value = key
      sortOrder.value = key === 'date' ? -1 : 1
    }
  }

  // Fuse instance for fuzzy searching across common transaction fields
  const fuse = computed(
    () =>
      new Fuse(transactions.value, {
        includeScore: true,
        shouldSort: true,
        keys: [
          'transaction_id',
          'date',
          'description',
          'merchant_name',
          'account_name',
          'institution_name',
          'category',
        ],
        threshold: 0.35,
        ignoreLocation: true,
      }),
  )

  const filteredTransactions = computed(() => {
    let items = transactions.value

    const query = searchQuery.value.trim()
    if (query) {
      // fzf-like narrowing; preserve Fuse order by score
      items = fuse.value.search(query).map((r) => r.item)
      // When searching, show all matches and skip pagination/padding
      return items
    }

    // Optional sort by column
    if (sortKey.value) {
      items = [...items].sort((a, b) => {
        const valA = a[sortKey.value] || ''
        const valB = b[sortKey.value] || ''
        if (sortKey.value === 'date') {
          const aTime = new Date(valA).getTime()
          const bTime = new Date(valB).getTime()
          return sortOrder.value === -1 ? bTime - aTime : aTime - bTime
        }
        if (typeof valA === 'number' && typeof valB === 'number') {
          return sortOrder.value === -1 ? valB - valA : valA - valB
        }
        return valA.toString().localeCompare(valB.toString()) * sortOrder.value
      })
    }

    // Promote a specific transaction id (e.g., from modal click)
    const promoteId = promoteIdRef?.value ? String(promoteIdRef.value) : null

    if (promoteId) {
      items = [...items].sort((a, b) => {
        const aMatch = String(a.transaction_id || '').includes(promoteId) ? 1 : 0
        const bMatch = String(b.transaction_id || '').includes(promoteId) ? 1 : 0
        return bMatch - aMatch // matches first, keep stable otherwise
      })
    }

    // Page slice with placeholder padding for consistent row height
    const pageItems = items.slice(0, pageSize)
    while (pageItems.length < pageSize) {
      pageItems.push({ _placeholder: true, transaction_id: `placeholder-${pageItems.length}` })
    }
    return pageItems
  })

  function formatCategory(tx) {
    const p = tx.primary_category || ''
    const d = tx.detailed_category || ''
    if (p && d) return `${p}: ${d}`
    if (p) return p
    if (d) return d
    // Fall back to the raw category string from the API so the table isn't blank.
    return tx.category || 'Uncategorized'
  }

  onMounted(() => {
    fetchTransactions(1, { force: true })
  })

  watch(
    () => currentPage.value,
    (page, previous) => {
      if (page === previous) return
      fetchTransactions(page)
    },
  )

  watch(
    filtersRef,
    () => {
      pageCache = new Map()
      lastTotal = 0
      totalPages.value = 1
      totalCount.value = 0
      if (currentPage.value !== 1) {
        currentPage.value = 1
      } else {
        fetchTransactions(1, { force: true })
      }
    },
    { deep: true },
  )

  if (targetTransactionIdRef) {
    watch(
      targetTransactionIdRef,
      () => {
        pageCache = new Map()
        fetchTransactions(currentPage.value, { force: true })
      },
      { immediate: false },
    )
  }

  return {
    transactions,
    searchQuery,
    sortKey,
    sortOrder,
    currentPage,
    totalPages,
    totalCount,
    fetchTransactions,
    isLoading,
    error,
    changePage,
    setPage,
    setSort,
    filteredTransactions,
    hasNextPage: computed(() => currentPage.value < totalPages.value),
  }
}
