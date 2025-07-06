/**
 * Transaction API helpers.
 *
 * Provides functions for retrieving and updating transaction data from the
 * backend. These utilities are consumed by composables and Vue components.
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
