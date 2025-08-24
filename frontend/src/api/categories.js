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
 * Fetch a flat list of categories with optional date and filter
 * parameters.
 *
 * @param {Object} params - Query parameters such as `start_date`,
 *   `end_date`, or search filters.
 */
export async function fetchCategories(params = {}) {
  const response = await axios.get('/api/categories', { params })
  return response.data
}
