/**
 * Account API helpers for summary and transaction lookups.
 *
 * Provides functions to retrieve net change summaries and recent
 * transactions for a given account.
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
