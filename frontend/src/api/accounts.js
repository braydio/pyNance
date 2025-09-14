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
 * @param {string|undefined} start - ISO start date.
 * @param {string|undefined} end - ISO end date.
 *
 * If start and end are omitted, they will be derived from a range string
 * (either provided as `start` or defaulting to `'30d'`) for backward
 * compatibility with previous range-based calls.
 */
export const fetchAccountHistory = async (accountId, start, end) => {
  let s = start
  let e = end
  if (!s || !e) {
    const range = typeof start === 'string' && !end ? start : '30d'
    ;({ start: s, end: e } = rangeToDates(range))
  }
  const params = { start_date: s, end_date: e }
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
