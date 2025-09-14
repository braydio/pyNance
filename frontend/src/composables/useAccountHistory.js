/**
 * Composable to fetch and expose balance history for a single account.
 * Results are memoized per account and range and can be refreshed manually.
 */
import { ref, isRef, watch } from 'vue'
import { fetchAccountHistory } from '@/api/accounts'

/**
 * Cache of previously fetched histories keyed by `${accountId}-${range}`.
 * @type {Map<string, Array>}
 */
const historyCache = new Map()

/**
 * Reactive helper to load recent balance history for an account.
 * @param {import('vue').Ref<string> | string} accountId
 * @param {import('vue').Ref<string> | string} rangeRef - reactive range string
 */
export function useAccountHistory(accountId, rangeRef) {
  const accountIdRef = isRef(accountId) ? accountId : ref(accountId)
  rangeRef = isRef(rangeRef) ? rangeRef : ref(rangeRef)
  const history = ref([])
  const loading = ref(false)

  // Load history for the provided date range. When `start` and `end` are
  // omitted, the current reactive range is converted to explicit dates.
  const fetchHistory = async (start, end, { force = false } = {}) => {
    if (!accountIdRef.value) return
    let s = start
    let e = end
    let rangeKey
    if (!s || !e) {
      rangeKey = typeof start === 'string' && !end ? start : range.value
      ;({ start: s, end: e } = rangeToDates(rangeKey))
    } else {
      rangeKey = `${s}-${e}`
    }
    const cacheKey = `${accountIdRef.value}-${rangeKey || ''}`
    if (!force && historyCache.has(cacheKey)) {
      history.value = historyCache.get(cacheKey)
      return
    }
    loading.value = true
    try {
      const response = await fetchAccountHistory(accountIdRef.value, s, e)
      let hist = []
      if (Array.isArray(response?.data?.history)) {
        hist = response.data.history
      } else if (Array.isArray(response?.history)) {
        hist = response.history
      } else if (Array.isArray(response?.data?.data?.history)) {
        hist = response.data.data.history
      }
      history.value = hist
      historyCache.set(cacheKey, hist)
    } catch (err) {
      console.error('Failed to load account history:', err)
    } finally {
      loading.value = false
    }
  }

  watch([accountIdRef, rangeRef], () => fetchHistory(), { immediate: true })

  const loadHistory = (start, end) => fetchHistory(start, end, { force: true })

  return {
    history,
    loading,
    loadHistory,
  }
}
