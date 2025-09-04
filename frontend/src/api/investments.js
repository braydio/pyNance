import axios from 'axios'

export const fetchInvestmentAccounts = async () => {
  const res = await axios.get('/api/investments/accounts')
  return res.data
}

export const fetchHoldings = async () => {
  const res = await axios.get('/api/investments/holdings')
  return res.data
}

export const fetchInvestmentTransactions = async (page = 1, pageSize = 25, filters = {}) => {
  const params = { page, page_size: pageSize, ...filters }
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
