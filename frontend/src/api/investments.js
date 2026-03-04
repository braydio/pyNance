import axios from 'axios'

export const fetchInvestmentAccounts = async (userId) => {
  const res = await axios.get('/api/investments/accounts', { params: { user_id: userId } })
  return res.data
}

export const fetchHoldings = async (userId) => {
  const res = await axios.get('/api/investments/holdings', { params: { user_id: userId } })
  return res.data
}

/**
 * Fetch paginated investment transactions with backend-aligned filter names.
 *
 * @param {number} [page=1] 1-indexed transaction page.
 * @param {number} [pageSize=25] Number of transactions per page.
 * @param {Object} [filters={}] Supported backend query filters.
 * @param {string} [filters.user_id] Plaid-backed user id.
 * @param {string} [filters.account_id] Investment account id.
 * @param {string} [filters.security_id] Security id.
 * @param {string} [filters.type] Transaction type.
 * @param {string} [filters.subtype] Transaction subtype.
 * @param {string} [filters.start_date] Inclusive start date (YYYY-MM-DD).
 * @param {string} [filters.end_date] Inclusive end date (YYYY-MM-DD).
 * @returns {Promise<Object>} API response payload.
 */
export const fetchInvestmentTransactions = async (page = 1, pageSize = 25, filters = {}) => {
  const { user_id, account_id, security_id, type, subtype, start_date, end_date } = filters
  const params = {
    page,
    page_size: pageSize,
    ...(user_id ? { user_id } : {}),
    ...(account_id ? { account_id } : {}),
    ...(security_id ? { security_id } : {}),
    ...(type ? { type } : {}),
    ...(subtype ? { subtype } : {}),
    ...(start_date ? { start_date } : {}),
    ...(end_date ? { end_date } : {}),
  }
  const res = await axios.get('/api/investments/transactions', { params })
  return res.data
}

export const refreshInvestments = async (user_id, item_id) => {
  const res = await axios.post('/api/plaid/investments/refresh', { user_id, item_id })
  return res.data
}

export const refreshInvestmentsAll = async (params = {}) => {
  const res = await axios.post('/api/plaid/investments/refresh_all', params)
  return res.data
}
