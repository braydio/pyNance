// src/api/accounts.js
import axios from 'axios'

export const getAccounts = async () => {
  const response = await axios.get('/api/accounts/list')
  return response.data
}

export const refreshAccounts = async () => {
  const response = await axios.get('/api/accounts/refresh_accounts')
  return response.data
}

export const deleteAccount = async (provider, account_id) => {
  const response = await axios.delete(`/api/accounts/delete`, {
    data: { provider, account_id }
  })
  return response.data
}
