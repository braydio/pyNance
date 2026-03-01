/**
 * Transaction API helpers.
 *
 * Provides functions for retrieving and updating transaction data from the
 * backend. These utilities are consumed by composables and Vue components.
 *
 * Exposed helpers:
 * - `fetchTransactions(params)` - paginated listing of transactions
 * - `updateTransaction(transactionData)` - modify a transaction
 * - `fetchTagSuggestions(q, limit?, user_id?)` - tag autocomplete list
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
 *   optional `tags` (array or comma-separated string), and an optional
 *   `category_ids` array or comma-separated string. Set `include_running_balance`
 *   to `true` only when the UI needs running balances returned. Provide
 *   `transaction_id` to fetch a specific transaction without altering the
 *   default pagination window.
 * @returns {Promise<Object>} Result containing a transactions array and total count.
 */
export const fetchTransactions = async (params = {}) => {
  const {
    category_ids,
    account_ids,
    tags,
    tag,
    merchant,
    include_running_balance = false,
    ...rest
  } = params
  const query = { ...rest }

  if (include_running_balance) {
    query.include_running_balance = include_running_balance
  }

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
  const tagFilters = tags ?? tag
  if (Array.isArray(tagFilters)) {
    query.tags = tagFilters.join(',')
  } else if (tagFilters) {
    query.tags = tagFilters
  }
  // Pass merchant filter directly to API
  if (merchant) {
    query.merchant = merchant
  }

  const response = await axios.get('/api/transactions/get_transactions', { params: query })
  return response.data?.status === 'success' ? response.data.data : { transactions: [], total: 0 }
}

/**
 * Update mutable transaction fields.
 *
 * Only ``date`` (YYYY-MM-DD), ``amount``, ``description``, ``category``,
 * ``merchant_name``, and optional ``tag`` or ``tags`` may be supplied along with
 * ``transaction_id``.
 *
 * @param {Object} transactionData - Transaction attributes to persist.
 * @returns {Promise<Object>} API response
 */
export const updateTransaction = async (transactionData) => {
  const response = await axios.put('/api/transactions/update', transactionData)
  return response.data
}

/**
 * Retrieve tag suggestions with optional substring filter.
 */
export const fetchTagSuggestions = async (q = '', limit = 50, user_id = '') => {
  const params = { q, limit }
  if (user_id) {
    params.user_id = user_id
  }
  const response = await axios.get('/api/transactions/tags', { params })
  return response.data?.status === 'success' ? response.data.data : []
}

/**
 * Retrieve merchant name suggestions with optional substring filter.
 */
export const fetchMerchantSuggestions = async (q = '', limit = 50) => {
  const response = await axios.get('/api/transactions/merchants', { params: { q, limit } })
  return response.data?.status === 'success' ? response.data.data : []
}

/**
 * Create a reusable transaction rule from a user edit.
 *
 * @param {Object} payload - { user_id, field, value, description, account_id }
 */
export const createTransactionRule = async (payload) => {
  const response = await axios.post('/api/transactions/rules', payload)
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
  try {
    const response = await axios.get('/api/transactions/top_merchants', { params })
    return response.data?.data || []
  } catch (error) {
    if (error?.response?.status !== 404) {
      throw error
    }
    // Backward-compatible fallback for backends that only expose charts routes.
    const response = await axios.get('/api/charts/merchant_breakdown', { params })
    const items = Array.isArray(response.data?.data) ? response.data.data : []
    return items.map((item) => ({
      name: item.label || 'Unknown',
      total: Number(item.amount) || 0,
      trend: [],
    }))
  }
}

/**
 * Fetch top categories by spending.
 *
 * @param {Object} params - Optional query params like `start_date` and `end_date`.
 * @returns {Promise<Array>} Array of category summaries.
 */
export const fetchTopCategories = async (params = {}) => {
  try {
    const response = await axios.get('/api/transactions/top_categories', { params })
    return response.data?.data || []
  } catch (error) {
    if (error?.response?.status !== 404) {
      throw error
    }
    // Backward-compatible fallback for backends that only expose charts routes.
    const response = await axios.get('/api/charts/category_breakdown', { params })
    const items = Array.isArray(response.data?.data) ? response.data.data : []
    return items.map((item) => ({
      name: item.category || 'Uncategorized',
      total: Number(item.amount) || 0,
      trend: [],
    }))
  }
}
