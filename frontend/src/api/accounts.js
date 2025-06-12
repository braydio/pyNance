// src/api/accounts.js
// Utility functions for interacting with the backend accounts endpoints.
import axios from 'axios'

export const getAccounts = async () => {
  const response = await axios.get('/api/accounts/get_accounts')
  return response.data
}

export const refreshAccounts = async () => {
  const response = await axios.post('/api/accounts/refresh_accounts')
  return response.data
}

export const deleteAccount = async (provider, account_id) => {
  const response = await axios.delete(`/api/accounts/delete`, {
    data: { provider, account_id }
  })
  return response.data
}
