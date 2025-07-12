/**
 * Account-related API helpers.
 *
 * Provides functions for retrieving net change summaries and recent
 * transactions for a single account.
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
