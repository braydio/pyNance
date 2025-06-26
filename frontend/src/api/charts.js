// src/api/transactions.js
import axios from 'axios'

export const fetchTransactions = async (page = 1, pageSize = 15) => {
  const response = await axios.get('/api/transactions/get_transactions', {
    params: { page, page_size: pageSize }
  })
  return response.data
}

export const updateTransaction = async (transactionData) => {
  const response = await axios.put('/api/transactions/update', transactionData)
  return response.data
}

export async function fetchCategoryBreakdownTree(params = {}) {
  const response = await axios.get('/api/charts/category_breakdown_tree', { params })
  return response.data
}
