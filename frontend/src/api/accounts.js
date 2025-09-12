/**
 * Account API helpers for account-centric lookups.
 *
 * Provides functions to retrieve balance history, net change summaries,
 * and recent transactions for a given account.
 */
import axios from 'axios'

export const fetchNetChanges = async (accountId, params = {}) => {
  const response = await axios.get(
    `/api/accounts/${accountId}/net_changes`,
    { params }
  )
  return response.data
}

export const fetchRecentTransactions = async (accountId, limit = 10) => {
  const params = { recent: true, limit }
  const response = await axios.get(
    `/api/transactions/${accountId}/transactions`,
    { params }
  )
  return response.data
}

/**
 * Fetch recent balance history for an account.
 *
 * @param {string} accountId
 * @param {object} [options]
 * @param {string} [options.range='30d'] - Range of days (e.g. '7d', '30d').
 * @param {string} [options.startDate] - Inclusive start date (YYYY-MM-DD).
 * @param {string} [options.endDate] - Inclusive end date (YYYY-MM-DD).
 */
export const fetchAccountHistory = async (
  accountId,
  { range = '30d', startDate, endDate } = {}
) => {
  const params = { range }
  if (startDate) params.start_date = startDate
  if (endDate) params.end_date = endDate
  const response = await axios.get(
    `/api/accounts/${accountId}/history`,
    { params }
  )
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
  const response = await axios.get(
    `/api/accounts/${accountId}/transaction_history`,
    { params }
  )
  return response.data
}
