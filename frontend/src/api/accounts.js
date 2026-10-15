/**
 * Account API helpers for account-centric lookups.
 *
 * Provides functions to retrieve balance history, net change summaries,
 * and recent transactions for a given account.
 */
import axios from 'axios'

export const fetchNetChanges = async (accountId, params = {}) => {
  const response = await axios.get(`/api/accounts/${accountId}/net_changes`, { params })
  const data = response.data || {}
  // Normalize into { status, data: { income, expense, net, money_in, money_out, net_movement, ... } }
  if (data.status === 'success' && data.data) return data
  // Legacy shape fallback: { account_id, net_change, period }
  const legacyNet = typeof data.net_change === 'number' ? data.net_change : 0
  return {
    status: 'success',
    data: { income: 0, expense: 0, net: legacyNet, balance_change: legacyNet },
  }
}

export const fetchRecentTransactions = async (accountId, limit = 10) => {
  const params = { recent: true, limit }
  const response = await axios.get(`/api/transactions/${accountId}/transactions`, { params })
  return response.data
}

/**
 * Format a Date as a local-calendar `YYYY-MM-DD` string (no UTC shift).
 *
 * @param {Date} date - Date to format.
 * @returns {string} Local ISO date.
 */
export function toLocalIsoDate(date) {
  const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/**
 * Convert a relative range string (e.g. `"30d"`) into inclusive local ISO dates.
 *
 * The window contains exactly `days` calendar days ending today: `30d` is today and the
 * 29 days before it.
 *
 * @param {string} range - Number of days followed by `d`.
 * @param {Date} [now] - Reference "today" (defaults to the current local date).
 * @returns {{ start: string, end: string }} Inclusive local start and end dates.
 */
export function rangeToDates(range = '30d', now = new Date()) {
  const days = Math.max(parseInt(range, 10) || 30, 1)
  const end = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const start = new Date(end.getFullYear(), end.getMonth(), end.getDate() - (days - 1))
  return { start: toLocalIsoDate(start), end: toLocalIsoDate(end) }
}

/**
 * Fetch per-account transaction counts and absolute values for an inclusive range.
 *
 * @param {{ start_date: string, end_date: string, account_ids?: string[]|string,
 *   include_hidden?: boolean, include_pending?: boolean, user_id?: string }} params
 * @returns {Promise<object>} `{ status, period, treatment, coverage, accounts }`.
 */
export const fetchAccountActivityBreakdown = async (params = {}) => {
  const { account_ids, ...rest } = params
  const query = { ...rest }
  if (Array.isArray(account_ids)) query.account_ids = account_ids.join(',')
  else if (account_ids) query.account_ids = account_ids
  const response = await axios.get('/api/accounts/activity_breakdown', { params: query })
  return response.data
}

/**
 * Fetch recent balance history for an account.
 *
 * @param {string} accountId
 * @param {string|object|undefined} start - ISO start date or legacy params object.
 * @param {string|undefined} end - ISO end date.
 *
 * If start and end are omitted, a `range` value may be supplied (either as the
 * second argument or within the legacy params object) and will be converted to
 * explicit dates for backward compatibility.
 */
export const fetchAccountHistory = async (accountId, start, end) => {
  let startDate = start
  let endDate = end

  // Support legacy calls where a params object with range or explicit dates was provided.
  if (typeof start === 'object' && start !== null) {
    const params = start
    if (params.start_date && params.end_date) {
      ;({ start_date: startDate, end_date: endDate } = params)
    } else if (params.range) {
      ;({ start: startDate, end: endDate } = rangeToDates(params.range))
    }
  }

  // Backward compatibility: allow passing a range string as the second arg.
  if (!startDate || !endDate) {
    const range = typeof start === 'string' && !end ? start : '30d'
    ;({ start: startDate, end: endDate } = rangeToDates(range))
  }

  const params = { start_date: startDate, end_date: endDate }
  const response = await axios.get(`/api/accounts/${accountId}/history`, { params })
  return response.data
}

/**
 * Fetch recent transaction history for an account (for sparklines).
 * Similar to daily net data but filtered for a specific account.
 *
 * @param {string} accountId
 * @param {object} params
 */
export const fetchAccountTransactionHistory = async (accountId, params = {}) => {
  const response = await axios.get(`/api/accounts/${accountId}/transaction_history`, { params })
  return response.data
}
