/**
 * Chart API helpers.
 *
 * Provides endpoints for retrieving data used by dashboard charts.
 * Includes category breakdowns and daily net values.
 */
import axios from 'axios'

// Tree (hierarchical) breakdown for the new chart
export async function fetchCategoryBreakdownTree(params = {}) {
  const response = await axios.get('/api/charts/category_breakdown_tree', { params })
  return response.data
}

/**
 * Aggregate spending by merchant name.
 *
 * @param {Object} params - Optional query params (e.g., `start_date`, `end_date`).
 * @returns {Promise<Object>} Merchant totals and metadata.
 */
export async function fetchMerchantBreakdown(params = {}) {
  const response = await axios.get('/api/charts/merchant_breakdown', { params })
  return response.data
}

// Old (flat) breakdown, if still needed. LOOK TO DEPRECATE
export async function fetchCategoryBreakdown(params = {}) {
  const response = await axios.get('/api/charts/category_breakdown', { params })
  return response.data
}

// For daily net chart
export async function fetchDailyNet(params = {}) {
  const response = await axios.get('/api/charts/daily_net', { params })
  return response.data
}
