// src/api/categories.js
// API helpers for category menu data
import axios from 'axios'

/**
 * Fetch hierarchical category tree for dropdown menus.
 * @returns {Promise<Object>} API response
 */
export async function fetchCategoryTree() {
  const response = await axios.get('/api/categories/tree')
  return response.data
}
