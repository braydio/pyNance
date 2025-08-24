// summary.js
// Helper for fetching financial summary metrics (totals, highest days, trend,
// volatility and outlier dates) from the backend.
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

export async function fetchFinancialSummary(params = {}) {
  const response = await apiClient.get('/summary/financial', { params })
  return response.data
}
