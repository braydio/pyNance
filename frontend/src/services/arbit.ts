/**
 * API helpers for arbitrage dashboard.
 */
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

/**
 * Fetch current arbitrage engine status.
 */
export async function fetchArbitStatus() {
  const response = await apiClient.get('/arbit/status')
  return response.data
}

/**
 * Retrieve profit and latency metrics.
 */
export async function fetchArbitMetrics() {
  const response = await apiClient.get('/arbit/metrics')
  return response.data
}

/**
 * Get the latest arbitrage opportunities.
 */
export async function fetchArbitOpportunities() {
  const response = await apiClient.get('/arbit/opportunities')
  return response.data
}

/**
 * Fetch recently executed arbitrage trades.
 */
export async function fetchArbitTrades() {
  const response = await apiClient.get('/arbit/trades')
  return response.data
}

/**
 * Start the arbitrage engine.
 */
export async function startArbit() {
  const response = await apiClient.post('/arbit/start')
  return response.data
}

/**
 * Stop the arbitrage engine.
 */
export async function stopArbit() {
  const response = await apiClient.post('/arbit/stop')
  return response.data
}

/**
 * Trigger an alert evaluation for net profit percentage.
 */
export async function postArbitAlert(threshold: number) {
  const response = await apiClient.post('/arbit/alerts', { threshold })
  return response.data
}
