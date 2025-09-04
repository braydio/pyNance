// File: src/composables/useTransactions.js

/**
 * Provides transaction table state and helpers for dashboard components.
 * Handles pagination, search, and sort logic while fetching from the API.
 */
import { ref, computed, onMounted } from 'vue'
import Fuse from 'fuse.js'
import { fetchTransactions as fetchTransactionsApi } from '@/api/transactions'

export function useTransactions(pageSize = 15, promoteIdRef = null) {
  const transactions = ref([])
  const searchQuery = ref('')
  const sortKey = ref(null)
  const sortOrder = ref(1)
  const currentPage = ref(1)
  const totalPages = ref(1)

  /**
   * Fetch a page of transactions from the API.
   *
   * Some backend responses omit the `status` field and return the data
   * object directly. This helper normalizes both shapes so the table renders
   * even when the backend does not include a status key.
   */
  const fetchTransactions = async () => {
    try {
      const res = await fetchTransactionsApi({
        page: currentPage.value,
        page_size: pageSize,
      })

      // No need to check for 'data' property
      if (!res || typeof res !== 'object' || !('transactions' in res)) {
        console.error('Unexpected response shape:', res)
        alert('Received an unexpected response from the server.')
        return
      }

      // normalize category fields for sorting/searching
      transactions.value = (res.transactions || []).map((tx) => ({
        ...tx,
        category: formatCategory(tx),
      }))
      const total = res.total != null ? res.total : 0
      totalPages.value = Math.max(1, Math.ceil(total / pageSize))
    } catch (error) {
      console.error('Error fetching transactions:', error)
    }
  }

  const changePage = (delta) => {
    currentPage.value = Math.max(1, Math.min(currentPage.value + delta, totalPages.value))
    fetchTransactions()
  }

  const setSort = (key) => {
    if (sortKey.value === key) {
      sortOrder.value *= -1
    } else {
      sortKey.value = key
      sortOrder.value = 1
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
    return p || d || ''
  }

  onMounted(fetchTransactions)

  return {
    transactions,
    searchQuery,
    sortKey,
    sortOrder,
    currentPage,
    totalPages,
    fetchTransactions,
    changePage,
    setSort,
    filteredTransactions,
  }
}
