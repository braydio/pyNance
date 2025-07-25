/**
 * Transaction API helpers.
 *
 * Provides functions for retrieving and updating transaction data from the
 * backend. These utilities are consumed by composables and Vue components.
 *
 * Exposed helpers:
 * - `fetchTransactions(params)` - paginated listing of transactions
 * - `updateTransaction(transactionData)` - modify a transaction
 * - `fetchRecentTransactions(accountId, limit?)` - newest transactions for an account
 * - `fetchNetChanges(accountId, params?)` - income/expense totals for an account
 */
import axios from 'axios'

export const fetchTransactions = async (params = {}) => {
  const response = await axios.get('/api/transactions/get_transactions', { params })
  return response.data
}

export const updateTransaction = async (transactionData) => {
  const response = await axios.put('/api/transactions/update', transactionData)
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

export const fetchNetChanges = async (accountId, params = {}) => {
  const response = await axios.get(
    `/api/accounts/${accountId}/net_changes`,
    { params }
  )
  return response.data
}
