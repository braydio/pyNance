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

/**
 * Fetch transactions from the backend.
 *
 * @param {Object} params - Query parameters such as `start_date`, `end_date`,
 *   and an optional `category_ids` array or comma-separated string.
 * @returns {Promise<Object>} Result containing a transactions array.
 */
export const fetchTransactions = async (params = {}) => {
  const { category_ids, ...rest } = params
  const query = { ...rest }

  // Allow callers to pass an array of IDs or a preformatted string
  if (Array.isArray(category_ids)) {
    query.category_ids = category_ids.join(',')
  } else if (category_ids) {
    query.category_ids = category_ids
  }

  const response = await axios.get('/api/transactions/get_transactions', { params: query })
  return (response.data?.status === 'success') ? response.data.data : { transactions: [] }
}

/**
 * Update mutable transaction fields.
 *
 * Only ``date`` (YYYY-MM-DD), ``amount``, ``description``, ``category`` and
 * ``merchant_name`` may be supplied along with ``transaction_id``.
 *
 * @param {Object} transactionData - Transaction attributes to persist.
 * @returns {Promise<Object>} API response
 */
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
