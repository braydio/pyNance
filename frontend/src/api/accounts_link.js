import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export default {
  async generateLinkToken(payload = {}) {
    const products = payload.products || []
    const isInvestments = products.length === 1 && products[0] === 'investments'
    const url = isInvestments
      ? '/plaid/investments/generate_link_token'
      : '/plaid/transactions/generate_link_token'

    const response = await apiClient.post(url, payload)
    return response.data
  },

  async exchangePublicToken(payload = {}) {
    const products = payload.products || []
    const url =
      products.length === 1 && products[0] === 'investments'
        ? '/plaid/investments/exchange_public_token'
        : '/plaid/transactions/exchange_public_token'

    const response = await apiClient.post(url, payload)
    return response.data
  },

  async deleteAccount(account_id) {
    if (!account_id) {
      throw new Error('account_id is required to delete an account')
    }

    try {
      const response = await apiClient.delete('/plaid/transactions/delete_account', {
        data: { account_id },
      })
      return response.data
    } catch (error) {
      console.error('Failed to delete account:', error)
      throw error
    }
  },
}
