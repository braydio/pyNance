import axios from 'axios'

/**
 * API helpers for Category resources.
 *
 * Exposes functions to retrieve category listings and the full
 * hierarchical tree used in dropdowns.
 */
export async function fetchCategoryTree(params = {}) {
  const response = await axios.get('/api/categories/tree', { params })
  return response.data
}

/**
 * Retrieve a flat list of categories.
 *
 * @param {Object} options - Query options.
 * @param {string} [options.start_date] - ISO start date filter.
 * @param {string} [options.end_date] - ISO end date filter.
 * @param {Object} [options.filters] - Additional search filters.
 */
export async function fetchCategories({ start_date, end_date, ...filters } = {}) {
  const params = { start_date, end_date, ...filters }
  const response = await axios.get('/api/categories', { params })
  return response.data
}
