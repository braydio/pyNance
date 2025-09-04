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
 * - `fetchTopMerchants(params?)` - highest spending merchants
 * - `fetchTopCategories(params?)` - highest spending categories
 */
import axios from 'axios'

/**
 * Fetch transactions from the backend with optional filters.
 *
 * @param {Object} params - Query parameters such as `start_date`, `end_date`,
 *   `account_ids` (array or comma-separated string), `tx_type` (credit|debit),
 *   and an optional `category_ids` array or comma-separated string.
 * @returns {Promise<Object>} Result containing a transactions array and total count.
 */
export const fetchTransactions = async (params = {}) => {
  const { category_ids, account_ids, ...rest } = params
  const query = { ...rest }

  // Allow callers to pass an array of IDs or a preformatted string
  if (Array.isArray(category_ids)) {
    query.category_ids = category_ids.join(',')
  } else if (category_ids) {
    query.category_ids = category_ids
  }
  if (Array.isArray(account_ids)) {
    query.account_ids = account_ids.join(',')
  } else if (account_ids) {
    query.account_ids = account_ids
  }

  const response = await axios.get('/api/transactions/get_transactions', { params: query })
  return response.data?.status === 'success' ? response.data.data : { transactions: [], total: 0 }
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
  const response = await axios.get(`/api/transactions/${accountId}/transactions`, { params })
  return response.data
}

export const fetchNetChanges = async (accountId, params = {}) => {
  const response = await axios.get(`/api/accounts/${accountId}/net_changes`, { params })
  return response.data
}

/**
 * Fetch top merchants by spending.
 *
 * @param {Object} params - Optional query params like `start_date` and `end_date`.
 * @returns {Promise<Array>} Array of merchant summaries.
 */
export const fetchTopMerchants = async (params = {}) => {
  const response = await axios.get('/api/transactions/top_merchants', { params })
  return response.data?.data || []
}

/**
 * Fetch top categories by spending.
 *
 * @param {Object} params - Optional query params like `start_date` and `end_date`.
 * @returns {Promise<Array>} Array of category summaries.
 */
export const fetchTopCategories = async (params = {}) => {
  const response = await axios.get('/api/transactions/top_categories', { params })
  return response.data?.data || []
}
