import axios from 'axios'

/**
 * API helpers for Category resources.
 * Currently exposes ``fetchCategoryTree`` to retrieve the full
 * category hierarchy for UI dropdowns.
 */
export async function fetchCategoryTree(params = {}) {
  const response = await axios.get('/api/categories/tree', { params })
  return response.data
}
