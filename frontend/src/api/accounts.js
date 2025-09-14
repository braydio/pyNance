/**
 * Account API helpers for account-centric lookups.
 *
 * Provides functions to retrieve balance history, net change summaries,
 * and recent transactions for a given account.
 */
import axios from 'axios'

export const fetchNetChanges = async (accountId, params = {}) => {
  const response = await axios.get(`/api/accounts/${accountId}/net_changes`, { params })
  return response.data
}

export const fetchRecentTransactions = async (accountId, limit = 10) => {
  const params = { recent: true, limit }
  const response = await axios.get(`/api/transactions/${accountId}/transactions`, { params })
  return response.data
}

/**
 * Convert a relative range string (e.g. `"30d"`) into ISO date strings.
 *
 * @param {string} range - Number of days followed by `d`.
 * @returns {{ start: string, end: string }} ISO start and end dates.
 */
export function rangeToDates(range = '30d') {
  const days = parseInt(range, 10) || 30
  const end = new Date()
  const start = new Date(end)
  start.setDate(start.getDate() - days)
  const toIso = (d) => d.toISOString().slice(0, 10)
  return { start: toIso(start), end: toIso(end) }
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
