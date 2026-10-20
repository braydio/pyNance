// File: src/composables/useTransactions.js

/**
 * Provides transaction table state and helpers for dashboard components.
 * Handles pagination, search, and sort logic while fetching from the API.
 * Supports dynamic filters via ``filtersRef`` (e.g., ``start_date`` or
 * ``account_ids``) which trigger refetches when changed. Search is a server-side filter over every
 * matching row; ``queryFilters`` is the one canonical filter set that the page request, the
 * all-matching summary and CSV export all share.
 */
import { ref, shallowRef, computed, onMounted, watch } from 'vue'
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
  // Server pages by number for the active filters; `currentPageRows` reads the page itself so a
  // jump to page 5 never depends on pages 2-4 having been loaded.
  const pageMap = shallowRef(new Map())
  const searchQuery = ref('')
  const sortKey = ref('date')
  const sortOrder = ref(-1)
  const currentPage = ref(1)
  const totalPages = ref(1)
  const totalCount = ref(0)
  const serverTotalRef = ref(0)
  const isLoading = ref(false)
  const error = ref(null)
  const highlightedTransaction = ref(null)

  const cacheStore = new Map()

  const PREFETCH_DEPTH = 3

  // Debounced so typing issues one request; clearing applies immediately.
  const appliedSearch = ref('')
  let searchTimer = null
  const SEARCH_DEBOUNCE_MS = 300

  /** The canonical server filter set: caller filters plus the applied search term. */
  const queryFilters = computed(() => {
    const filters = { ...(filtersRef.value || {}) }
    const term = appliedSearch.value.trim()
    if (term) filters.search = term
    return filters
  })

  /** Stable key for the canonical filter set (also used to discard stale responses). */
  const filterHash = computed(() => {
    const filters = queryFilters.value
    return JSON.stringify(
      Object.keys(filters)
        .sort()
        .reduce((acc, key) => {
          acc[key] = filters[key]
          return acc
        }, {}),
    )
  })

  const cacheKey = computed(() => {
    const filters = queryFilters.value
    const sorted = Object.keys(filters)
      .sort()
      .reduce((acc, key) => {
        acc[key] = filters[key]
        return acc
      }, {})
    return JSON.stringify(sorted)
  })

  const ensureBucket = () => {
    const key = cacheKey.value
    if (!cacheStore.has(key)) {
      cacheStore.set(key, { pages: new Map(), lastTotal: 0, prefetching: new Set() })
    }
    return cacheStore.get(key)
  }

  const serverTotal = computed(
    () => cacheStore.get(cacheKey.value)?.lastTotal || serverTotalRef.value || 0,
  )

  const { includeRunningBalance = false } = options

  const targetTransactionIdRef = options.targetTransactionIdRef || null

  const targetTransactionId = computed(() => {
    if (!targetTransactionIdRef) return ''
    return targetTransactionIdRef.value ? String(targetTransactionIdRef.value) : ''
  })

  /**
   * Normalize a collection of transactions for table consumption.
   *
   * @param {Array<Object>} items - Raw API transactions.
   * @returns {Array<Object>} Transactions with formatted categories.
   */
  function normalizeTransactions(items = []) {
    return items.map((tx) => ({
      ...tx,
      category: formatCategory(tx),
    }))
  }

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
        ...queryFilters.value,
      })

      if (!res || !Array.isArray(res.transactions) || res.transactions.length === 0) {
        return null
      }

      return normalizeTransactions(res.transactions)[0]
    } catch (err) {
      console.warn('Unable to fetch targeted transaction', err)
      return null
    }
  }

  /**
   * Rebuild the unpaginated transaction collection from cached pages.
   *
   * The cache stores normalized pages keyed by page number. Flattening the map
   * ensures that client-side filters (search, sort, promote) operate on all
   * known pages rather than a single page of results.
   *
   * @param {Map<number, Array>} pageCache - Cached page map for the active filter set.
   */
  function refreshTransactionsFromCache(pageCache) {
    const orderedPages = Array.from(pageCache.entries()).sort(([a], [b]) => a - b)
    const seen = new Set()
    const combined = []

    orderedPages.forEach(([, pageTransactions]) => {
      pageTransactions.forEach((tx) => {
        const key = String(tx.transaction_id || tx.id || combined.length)
        if (seen.has(key)) return
        seen.add(key)
        combined.push(tx)
      })
    })

    const targetTx = highlightedTransaction.value
    if (targetTx) {
      const targetKey = String(targetTx.transaction_id || targetTx.id || 'target')
      if (!seen.has(targetKey)) {
        combined.unshift(targetTx)
      }
    }

    transactions.value = combined
    pageMap.value = new Map(pageCache)
  }

  /**
   * Synchronize pagination metadata with the server-reported matching total.
   *
   * Search and every other filter run on the server across all matching rows, so the total never
   * has to be derived from the rows that happen to be loaded.
   */
  function updatePaginationMeta() {
    const derivedTotal = Math.max(serverTotal.value || 0, 0)

    totalCount.value = derivedTotal
    totalPages.value = Math.max(1, Math.ceil(derivedTotal / pageSize))

    if (currentPage.value > totalPages.value) {
      currentPage.value = totalPages.value
    }
  }

  /**
   * Request a page of transactions from the backend using the current filters.
   *
   * @param {number} page - Page number to request.
   * @returns {Promise<Object>} Raw API response containing transactions and totals.
   */
  function fetchPageData(page) {
    return fetchTransactionsApi({
      page,
      page_size: pageSize,
      ...(includeRunningBalance ? { include_running_balance: true } : {}),
      ...queryFilters.value,
    })
  }

  /**
   * Load a page into the cache and update totals.
   *
   * @param {Map<string, *>} bucket - Cache bucket for the active filter set.
   * @param {number} page - Page number to load.
   * @returns {Promise<Array<Object>>} Normalized transactions for the page.
   */
  async function loadPage(bucket, page) {
    const requestedHash = filterHash.value
    const res = await fetchPageData(page)
    if (requestedHash !== filterHash.value) {
      // Filters changed while this request was in flight: its rows belong to a different query.
      return []
    }
    if (!res || typeof res !== 'object' || !('transactions' in res)) {
      throw new Error('Received an unexpected response from the server.')
    }

    const normalised = normalizeTransactions(res.transactions || [])
    const responseTotal = res.total != null ? res.total : normalised.length

    bucket.pages.set(page, normalised)
    bucket.lastTotal = responseTotal
    serverTotalRef.value = responseTotal

    return normalised
  }

  /**
   * Determine the maximum page number based on the server-reported total.
   *
   * @param {Map<string, *>} bucket - Cache bucket for the active filter set.
   * @returns {number} Maximum page number indicated by the current total.
   */
  function maxServerPage(bucket) {
    return Math.max(1, Math.ceil((bucket.lastTotal || 0) / pageSize))
  }

  const fetchTransactions = async (page = currentPage.value, { force = false } = {}) => {
    const bucket = ensureBucket()
    const hasCachedPage = bucket.pages.has(page)

    isLoading.value = true
    error.value = null

    try {
      const targetTx = await fetchTargetTransaction(targetTransactionId.value)
      highlightedTransaction.value = targetTx

      const requestedHash = filterHash.value
      if (!hasCachedPage || force) {
        await loadPage(bucket, page)
      }
      if (requestedHash !== filterHash.value) return

      refreshTransactionsFromCache(bucket.pages)
      updatePaginationMeta()
      prefetchNeighborPages(bucket, page, maxServerPage(bucket), cacheKey.value)
    } catch (err) {
      console.error('Error fetching transactions:', err)
      error.value = err instanceof Error ? err : new Error('Unable to load transactions')
      transactions.value = []
      totalPages.value = 1
      totalCount.value = 0
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

  /** Order loaded rows: optional column sort, then promote a requested transaction id. */
  function orderRows(source) {
    let items = source

    // Search narrows on the server, so the loaded rows are only ordered here.
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

    return items
  }

  const filteredTransactions = computed(() => orderRows(transactions.value))

  /** Rows of the current server page only (plus a targeted transaction on page 1). */
  const currentPageRows = computed(() => {
    const rows = pageMap.value.get(currentPage.value) || []
    const target = highlightedTransaction.value
    const withTarget =
      target &&
      currentPage.value === 1 &&
      !rows.some((tx) => tx.transaction_id === target.transaction_id)
        ? [target, ...rows]
        : rows
    return orderRows(withTarget)
  })

  const paginatedTransactions = computed(() => {
    const start = (currentPage.value - 1) * pageSize
    return filteredTransactions.value.slice(start, start + pageSize)
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

  watch(searchQuery, (value) => {
    clearTimeout(searchTimer)
    if (!String(value || '').trim()) {
      appliedSearch.value = ''
      return
    }
    searchTimer = setTimeout(() => {
      appliedSearch.value = String(value)
    }, SEARCH_DEBOUNCE_MS)
  })

  watch(filterHash, () => {
    cacheStore.clear() // reset buckets for new filters
    highlightedTransaction.value = null
    transactions.value = []
    pageMap.value = new Map()
    totalPages.value = 1
    totalCount.value = 0
    serverTotalRef.value = 0
    if (currentPage.value !== 1) {
      currentPage.value = 1
    } else {
      fetchTransactions(1, { force: true })
    }
  })

  async function prefetchNeighborPages(bucket, current, total, bucketKey) {
    const upper = Math.min(total, PREFETCH_DEPTH)
    const targets = []
    for (let p = current + 1; p <= upper; p += 1) {
      if (bucket.pages.has(p) || bucket.prefetching.has(p)) continue
      targets.push(p)
      bucket.prefetching.add(p)
    }
    if (!targets.length) return

    await Promise.allSettled(
      targets.map(async (page) => {
        try {
          await loadPage(bucket, page)
          if (cacheKey.value === bucketKey) {
            refreshTransactionsFromCache(bucket.pages)
            updatePaginationMeta()
          }
        } catch (prefetchErr) {
          console.warn('Prefetch page failed', prefetchErr)
        } finally {
          bucket.prefetching.delete(page)
        }
      }),
    )
  }

  if (targetTransactionIdRef) {
    watch(
      targetTransactionIdRef,
      () => {
        cacheStore.clear()
        highlightedTransaction.value = null
        fetchTransactions(currentPage.value, { force: true })
      },
      { immediate: false },
    )
  }

  watch([filteredTransactions, serverTotal], updatePaginationMeta, {
    immediate: true,
  })

  return {
    transactions,
    searchQuery,
    queryFilters,
    filterHash,
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
    currentPageRows,
    paginatedTransactions,
    hasNextPage: computed(() => currentPage.value < totalPages.value),
  }
}
