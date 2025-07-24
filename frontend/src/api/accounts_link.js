import axios from "axios"

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL || "/api",
  headers: {
    "Content-Type": "application/json",
  },
})

export default {
  async generateLinkToken(provider, payload = {}) {
    let url = ""
    if (provider === "plaid") {
      const products = payload.products || []
      const isInvestments = products.length === 1 && products[0] === "investments"
      url = isInvestments
        ? "/plaid/investments/generate_link_token"
        : "/plaid/transactions/generate_link_token"
    } else if (provider === "teller") {
      url = "/teller/transactions/generate_link_token"
    }
    const response = await apiClient.post(url, payload)
    return response.data
  },

  async saveTellerToken(data) {
    const response = await apiClient.post("/teller/token", data)
    return response.data
  },

  async exchangePublicToken(provider, payload) {
    if (provider === "teller") {
      console.warn("Teller does not use public token exchange.")
      return { error: "Not supported for Teller" }
    }
    let url = `/${provider}/transactions/exchange_public_token`
    if (provider === "plaid") {
      const products = payload.products || []
      if (products.length === 1 && products[0] === "investments") {
        url = "/plaid/investments/exchange_public_token"
      }
    }
    const response = await apiClient.post(url, payload)
    return response.data
  },

  async deleteAccount(provider, account_id) {
    const urlMap = {
      plaid: "/plaid/transactions/delete_account",
      teller: "/teller/transactions/delete_account",
    }
    const url = urlMap[provider]
    if (!url) return

    try {
      const response = await apiClient.delete(url, { data: { account_id } })
      return response.data
    } catch (error) {
      console.error("Failed to delete account:", error)
      throw error
    }
  },
}
