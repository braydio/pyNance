
import axios from "axios";

// Base client using Vite environment variable
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL || "http://localhost:5000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

export default {
  async getAccounts() {
    const response = await apiClient.get("/accounts/get_accounts");
    return response.data;
  },
  async refreshAccounts() {
    const response = await apiClient.post("/teller/transactions/refresh_balances");
    return response.data;
  },
  async fetchTransactions(page = 1, pageSize = 50) {
    const response = await apiClient.get(`/transactions/get_transactions?page=${page}&page_size=${pageSize}`);
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
    const response = await apiClient.put("/transactions/update", transactionData);
    return response.data;
  },
  async generateLinkToken(provider, payload = {}) {
    const url = provider === "plaid"
      ? "/plaid/transactions/generate_link_token"
      : "/teller/transactions/generate_link_token";
    const response = await apiClient.post(url, payload);
    return response.data;
  },
  async saveTellerToken(data) {
    const response = await apiClient.post("/teller/transactions/token", data);
    return response.data;
  },
  async exchangePublicToken(provider, payload) {
    if (provider === "teller") {
      console.warn("Teller does not use exchangePublicToken");
      return { error: "Not supported" };
    }
    const response = await apiClient.post(`/${provider}/transactions/exchange_public_token`, payload);
    return response.data;
  },
  async deleteAccount(provider, account_id) {
    const url = provider === "plaid"
      ? "/plaid/transactions/delete_account"
      : "/teller/transactions/delete_account";
    const response = await apiClient.delete(url, { data: { account_id } });
    return response.data;
  },
  async fetchRecurringTransactions(account_id) {
    const response = await apiClient.get(`/accounts/${account_id}/recurring`);
    return response.data;
  },
  async updateRecurringTransaction(account_id, payload) {
    const response = await apiClient.put(`/accounts/${account_id}/recurringTx`, payload);
    return response.data;
  },
  async createRecurringTransaction(transactionId, payload) {
    const response = await apiClient.post(`/transactions/${transactionId}/recurring`, payload);
    return response.data;
  },
};

