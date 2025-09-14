/**
 * Composable to fetch and expose balance history for a single account.
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
  const range = isRef(rangeRef) ? rangeRef : ref(rangeRef)
  const history = ref([])
  const loading = ref(false)

  const fetchHistory = async (start, end, { force = false } = {}) => {
    if (!accountIdRef.value) return
    const rangeKey = start && end ? `${start}-${end}` : range.value
    const cacheKey = `${accountIdRef.value}-${rangeKey || ''}`
    if (!force && historyCache.has(cacheKey)) {
      history.value = historyCache.get(cacheKey)
      return
    }
    loading.value = true
    try {
      const options =
        start && end ? { start_date: start, end_date: end } : { range: rangeKey }
      const response = await fetchAccountHistory(accountIdRef.value, options)
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

  watch([accountIdRef, range], () => fetchHistory(), { immediate: true })

  const loadHistory = (start, end) => fetchHistory(start, end, { force: true })

  return {
    history,
    loading,
    loadHistory,
  }
}
