/**
 * Summary API helpers.
 *
 * Provides endpoints for retrieving financial summary metrics including
 * highest income/expense day, trend, volatility, and detected outlier days.
 */
import axios from 'axios'

export async function fetchFinancialSummary(params = {}) {
  const response = await axios.get('/api/summary/financial', { params })
  return response.data
}
