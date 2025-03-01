// src/services/api.js
import axios from "axios";

// Use Vite's environment variables via import.meta.env
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL || "http://localhost:5000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

export default {
  async getAccounts() {
    const response = await apiClient.get("/teller/transactions/get_accounts");
    return response.data;
  },
  async refreshAccounts() {
    const response = await apiClient.post("/teller/transactions/refresh_balances");
    return response.data;
  },
  async fetchTransactions(page = 1, pageSize = 50) {
    const response = await apiClient.get(
      `/transactions/get_transactions?page=${page}&page_size=${pageSize}`
    );
    return response.data;
  },
  async fetchCategoryBreakdown() {
    const response = await apiClient.get("/charts/category_breakdown");
    return response.data;
  },
  async fetchDailyNet() {
    const response = await apiClient.get("/charts/daily_net");
    return response.data;
  },
  async fetchNetAssets() {
    const response = await apiClient.get("/charts/net_assets");
    return response.data;
  },
  async updateTransaction(transactionData) {
    const response = await apiClient.put("/teller/transactions/update", transactionData);
    return response.data;
  },
  /**
   * Generate a link token for a given provider.
   * provider: "plaid" or "teller"
   */
  async generateLinkToken(provider, payload = {}) {
    let url = "";
    if (provider === "plaid") {
      url = "/plaid/transactions/generate_link_token";
    } else if (provider === "teller") {
      url = "/teller/transactions/generate_link_token";
    }
    const response = await apiClient.post(url, payload);
    return response.data;
  },
  /**
   * Exchange a public token for an access token.
   * provider: "plaid" or "teller"
   */
  async exchangePublicToken(provider, public_token) {
    let url = "";
    if (provider === "plaid") {
      url = "/plaid/transactions/exchange_public_token";
    } else if (provider === "teller") {
      url = "/teller/transactions/exchange_public_token";
    }
    const response = await apiClient.post(url, { public_token, provider });
    return response.data;
  },
};
