/**
 * Composable to fetch and expose transaction history for a single account.
 * Similar to DailyNet data but filtered for a specific account.
 */
import { ref, isRef, watch } from 'vue'
import { fetchAccountTransactionHistory } from '@/api/accounts'

/**
 * Convert an arbitrary date-like value into an ISO `YYYY-MM-DD` key.
 *
 * @param {unknown} value
 * @returns {string|null}
 */
function toDateKey(value) {
  if (!value) return null
  if (typeof value === 'string') {
    return value.slice(0, 10)
  }
  if (value instanceof Date) {
    return value.toISOString().slice(0, 10)
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return date.toISOString().slice(0, 10)
}

/**
 * Ensure numeric coercion for transaction amount-like fields.
 *
 * @param {unknown} value
 * @returns {number}
 */
function toNumber(value) {
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
 * Aggregate transactions by day into net amounts and counts.
 *
 * @param {Array} transactions
 * @returns {Array<{ date: string, net_amount: number, transaction_count: number }>}
 */
function aggregateTransactions(transactions) {
  if (!Array.isArray(transactions) || !transactions.length) {
    return []
  }

  const byDate = new Map()

  for (const tx of transactions) {
    if (!tx || typeof tx !== 'object') continue
    const date =
      toDateKey(tx.date) ||
      toDateKey(tx.transaction_date) ||
      toDateKey(tx.datetime) ||
      toDateKey(tx.authorized_date)
    if (!date) continue

    const amount = toNumber(tx.net_amount ?? tx.amount ?? tx.value ?? tx.net ?? tx.total)
    const count =
      typeof tx.transaction_count === 'number'
        ? tx.transaction_count
        : Array.isArray(tx.transactions)
          ? tx.transactions.length
          : 1

    const summary = byDate.get(date) || { net_amount: 0, transaction_count: 0 }
    summary.net_amount += amount
    summary.transaction_count += Number.isFinite(count) && count > 0 ? count : 1
    byDate.set(date, summary)
  }

  return Array.from(byDate.entries())
    .sort(([a], [b]) => (a > b ? 1 : a < b ? -1 : 0))
    .map(([date, summary]) => ({
      date,
      net_amount: Math.round(summary.net_amount * 100) / 100,
      transaction_count: summary.transaction_count,
    }))
}

/**
 * Normalize the transaction history payload returned by the API.
 *
 * The endpoint currently returns raw transactions. Older payloads may expose
 * the same array nested under different keys or already provide a normalized
 * `history` list. This helper consolidates all known shapes into a uniform
 * array of `{ date, net_amount, transaction_count }` objects ordered
 * chronologically.
 *
 * @param {unknown} payload
 * @returns {Array<{ date: string, net_amount: number, transaction_count: number }>}
 */
function normalizeTransactionHistoryPayload(payload) {
  if (!payload || typeof payload !== 'object') {
    return []
  }

  const historyCandidates = [payload.history, payload?.data?.history, payload?.data?.data?.history]

  for (const candidate of historyCandidates) {
    if (Array.isArray(candidate) && candidate.length) {
      const normalized = aggregateTransactions(candidate)
      if (normalized.length) {
        return normalized
      }
    }
  }

  const transactionCandidates = [
    payload.transactions,
    payload?.data?.transactions,
    payload?.data?.data?.transactions,
  ]

  for (const candidate of transactionCandidates) {
    if (Array.isArray(candidate) && candidate.length) {
      const normalized = aggregateTransactions(candidate)
      if (normalized.length) {
        return normalized
      }
    }
  }

  return []
}

/**
 * Reactive helper to load recent transaction history for an account.
 * @param {import('vue').Ref<string> | string} accountId
 */
export function useAccountTransactionHistory(accountId) {
  const accountIdRef = isRef(accountId) ? accountId : ref(accountId)
  const history = ref([])
  const loading = ref(false)

  const fetchHistory = async () => {
    if (!accountIdRef.value) return
    loading.value = true
    try {
      const response = await fetchAccountTransactionHistory(accountIdRef.value)
      history.value = normalizeTransactionHistoryPayload(response)
    } catch (err) {
      console.error('Failed to load account transaction history:', err)
      // Fallback to empty array to prevent sparkline errors
      history.value = []
    } finally {
      loading.value = false
    }
  }

  watch(accountIdRef, fetchHistory, { immediate: true })

  return {
    history,
    loading,
    fetchHistory,
  }
}
