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
 * @param {object} params
 */
export const fetchAccountHistory = async (accountId, params = {}) => {
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
