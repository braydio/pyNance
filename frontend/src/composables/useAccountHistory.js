/**
 * Composable to fetch and expose normalized account history for a single account.
 * Results are memoized per account/date-range and can be refreshed manually.
 */
import { ref, isRef, watch, computed } from 'vue'
import { fetchAccountHistory, rangeToDates } from '@/api/accounts'

/**
 * @typedef {{ date: string, balance: number }} NormalizedHistoryPoint
 */

/**
 * Cache of previously fetched histories keyed by `${accountId}-${start}-${end}`.
 * @type {Map<string, Array<NormalizedHistoryPoint>>}
 */
const historyCache = new Map()

/**
 * In-flight request cache to prevent duplicate fetches for the same account/range pair.
 * @type {Map<string, Promise<Array<NormalizedHistoryPoint>>>}
 */
const inFlightHistoryRequests = new Map()

/**
 * Parse a value into a finite number with a zero fallback.
 *
 * @param {unknown} value
 * @returns {number}
 */
function toFiniteNumber(value) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }

  if (typeof value === 'string') {
    const parsed = Number.parseFloat(value)
    return Number.isFinite(parsed) ? parsed : 0
  }

  return 0
}

/**
 * Normalize a single history entry.
 *
 * @param {unknown} point
 * @returns {NormalizedHistoryPoint|null}
 */
function normalizeHistoryPoint(point) {
  if (!point || typeof point !== 'object') {
    return null
  }

  const dateValue = point.date ?? point.as_of ?? point.timestamp
  if (typeof dateValue !== 'string' || !dateValue.trim()) {
    return null
  }

  const date = dateValue.slice(0, 10)
  return {
    date,
    balance: toFiniteNumber(point.balance ?? point.amount ?? point.value ?? point.net),
  }
}

/**
 * Normalize the account history payload returned by the API.
 *
 * The API now returns `balances` as the canonical property but older
 * responses surfaced the same data under `history` within different
 * nesting levels. The composable always works with the normalized list.
 *
 * @param {unknown} payload - Raw payload returned from `fetchAccountHistory`.
 * @returns {Array<NormalizedHistoryPoint>} Normalized history array.
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
        .map(normalizeHistoryPoint)
        .filter((point) => point !== null)
        .sort((left, right) => left.date.localeCompare(right.date))
    }
  }

  return []
}

/**
 * Resolve start/end dates from explicit values or a range key.
 *
 * @param {string|undefined} start
 * @param {string|undefined} end
 * @param {string} rangeKey
 * @returns {{ start: string, end: string }}
 */
function resolveDateWindow(start, end, rangeKey) {
  if (start && end) {
    return { start, end }
  }

  return rangeToDates(rangeKey)
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
  const error = ref(null)
  const isReady = computed(() => !loading.value && !error.value)

  // Load history for the provided date range. When `start` and `end` are
  // omitted, the current reactive range is converted to explicit dates.
  const fetchHistory = async (start, end, { force = false } = {}) => {
    if (!accountIdRef.value) {
      history.value = []
      error.value = null
      return []
    }

    const rangeKey = typeof start === 'string' && !end ? start : rangeRef.value || '30d'
    const { start: s, end: e } = resolveDateWindow(start, end, rangeKey)
    const cacheKey = `${accountIdRef.value}-${s}-${e}`

    if (!force && historyCache.has(cacheKey)) {
      history.value = historyCache.get(cacheKey)
      error.value = null
      return history.value
    }

    if (!force && inFlightHistoryRequests.has(cacheKey)) {
      history.value = await inFlightHistoryRequests.get(cacheKey)
      return history.value
    }

    loading.value = true
    error.value = null

    const request = fetchAccountHistory(accountIdRef.value, s, e).then((response) => {
      const hist = normalizeHistoryPayload(response)
      historyCache.set(cacheKey, hist)
      return hist
    })

    inFlightHistoryRequests.set(cacheKey, request)

    try {
      const hist = await request
      history.value = hist
      return hist
    } catch (err) {
      console.error('Failed to load account history:', err)
      error.value = err
      history.value = []
      return []
    } finally {
      inFlightHistoryRequests.delete(cacheKey)
      loading.value = false
    }
  }

  watch([accountIdRef, rangeRef], () => fetchHistory(), { immediate: true })

  const loadHistory = (start, end) => fetchHistory(start, end, { force: true })

  return {
    history,
    balances,
    loading,
    error,
    isReady,
    loadHistory,
  }
}
