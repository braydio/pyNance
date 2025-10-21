/**
 * Composable to fetch and expose balance history for a single account.
 * Results are memoized per account and range and can be refreshed manually.
 */
import { ref, isRef, watch } from 'vue'
import { fetchAccountHistory, rangeToDates } from '@/api/accounts'

/**
 * Cache of previously fetched histories keyed by `${accountId}-${range}`.
 * @type {Map<string, Array>}
 */
const historyCache = new Map()

/**
 * Normalize the account history payload returned by the API.
 *
 * The API now returns `balances` as the canonical property but older
 * responses surfaced the same data under `history` within different
 * nesting levels. The composable always works with the normalized list.
 *
 * @param {unknown} payload - Raw payload returned from `fetchAccountHistory`.
 * @returns {Array} Normalized history array.
 */
function normalizeHistoryPayload(payload) {
  if (!payload || typeof payload !== 'object') {
    return []
  }

  const candidates = [
    payload.balances,
    payload.history,
    payload?.data?.balances,
    payload?.data?.history,
    payload?.data?.data?.balances,
    payload?.data?.data?.history,
  ]

  for (const candidate of candidates) {
    if (Array.isArray(candidate)) {
      return candidate
    }
  }

  return []
}

/**
 * Reactive helper to load recent balance history for an account.
 * @param {import('vue').Ref<string> | string} accountId
 * @param {import('vue').Ref<string> | string} rangeRef - reactive range string
 */
export function useAccountHistory(accountId, rangeRef) {
  const accountIdRef = isRef(accountId) ? accountId : ref(accountId)
  rangeRef = isRef(rangeRef) ? rangeRef : ref(rangeRef)
  const history = ref([])
  const balances = history
  const loading = ref(false)

  // Load history for the provided date range. When `start` and `end` are
  // omitted, the current reactive range is converted to explicit dates.
  const fetchHistory = async (start, end, { force = false } = {}) => {
    if (!accountIdRef.value) return
    let s = start
    let e = end
    let rangeKey
    if (!s || !e) {
      rangeKey = typeof start === 'string' && !end ? start : rangeRef.value
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
      const hist = normalizeHistoryPayload(response)
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
    balances,
    loading,
    loadHistory,
  }
}
