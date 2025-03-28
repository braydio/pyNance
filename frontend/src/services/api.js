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
  async getAccounts(provider = "teller") {
    // Uses the new generic accounts endpoint with a provider query parameter.
    const response = await apiClient.get(`/accounts/get_accounts?provider=${provider}`);
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

  async exchangePublicToken(provider, payload) {
    const response = await apiClient.post(
      `/${provider}/transactions/exchange_public_token`,
      payload
    );
    return response.data;
  },
  

  async deleteAccount(provider, account_id) {
    let url = "";
    if (provider === "plaid") {
      url = "/plaid/transactions/delete_account";
    } else if (provider === "teller") {
      url = "/teller/transactions/delete_account";
    }
    const response = await apiClient.delete(url, {
      data: { account_id },
    });
    return response.data;
  },
  async fetchRecurringTransactions(provider, account_id) {
    // This now calls the new generic recurring endpoint.
    const response = await apiClient.get(`/accounts/${account_id}/recurring`);
    return response.data;
  },
  async updateRecurringTransaction(account_id, payload) {
    // This calls the new recurringTx update endpoint.
    const response = await apiClient.put(`/accounts/${account_id}/recurringTx`, payload);
    return response.data;
  },
};
