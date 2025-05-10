
// src/api/charts.js
import axios from 'axios'

export const fetchCategoryBreakdown = async () => {
  const response = await axios.get('/api/charts/category_breakdown')
  return response.data
}

export const fetchDailyNet = async () => {
  const response = await axios.get('/api/charts/daily_net')
  return response.data
}

export const fetchNetAssets = async () => {
  const response = await axios.get('/api/charts/net_assets')
  return response.data
}

