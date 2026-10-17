// src/api/recurring.js
import axios from 'axios'

const BASE = '/api/recurring'

/** List recurring streams. Params: status (comma list), account_id, page, page_size (20-100). */
export const getRecurringStreams = async (params = {}) => {
  const response = await axios.get(`${BASE}/streams`, { params })
  return response.data
}

/** Detected suggestions awaiting review. Params: account_id, include_ignored. */
export const getRecurringCandidates = async (params = {}) => {
  const response = await axios.get(`${BASE}/candidates`, { params })
  return response.data
}

/**
 * Look for recurring patterns in stored history. Read-only unless `dry_run` is false, in which case
 * proposals are saved (never confirmed) in one transaction.
 */
export const scanRecurring = async (body = {}) => {
  const response = await axios.post(`${BASE}/scan`, body)
  return response.data
}

/** Create a manual plan: { account_id, display_name, amount_cash_delta, cadence, anchor_date, ... }. */
export const createRecurringStream = async (payload) => {
  const response = await axios.post(`${BASE}/streams`, payload)
  return response.data
}

export const updateRecurringStream = async (streamId, payload) => {
  const response = await axios.patch(`${BASE}/streams/${streamId}`, payload)
  return response.data
}

/** Record a durable decision: 'confirmed' | 'ignored' | 'ended'. */
export const decideRecurringStream = async (streamId, decision) => {
  const response = await axios.post(`${BASE}/streams/${streamId}/decision`, { decision })
  return response.data
}

/** End a stream (history kept). Pass { hard: true } to remove it. Transactions are never deleted. */
export const endRecurringStream = async (streamId, { hard = false } = {}) => {
  const response = await axios.delete(`${BASE}/streams/${streamId}`, { params: { hard } })
  return response.data
}

// --- Compatibility: older callers (reminders for the next seven days). ---

export const getRecurringTransactions = async (accountId) => {
  const response = await axios.get(`${BASE}/${accountId}/recurring`)
  return response.data
}

/**
 * Create or update a user-defined recurring transaction (legacy shape).
 */
export const saveRecurringTransaction = async (accountId, payload) => {
  const response = await axios.put(`${BASE}/accounts/${accountId}/recurringTx`, payload)
  return response.data
}

export const createRecurringTransaction = async (transactionId, payload) => {
  const response = await axios.post(`/api/transactions/${transactionId}/recurring`, payload)
  return response.data
}

export const scanRecurringTransactions = async (accountId) => {
  const response = await axios.post(`${BASE}/scan/${accountId}`)
  return response.data
}
