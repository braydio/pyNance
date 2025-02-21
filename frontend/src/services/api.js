// src/services/api.js
import axios from "axios";

// Create an Axios instance; adjust the base URL as needed.
const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || "http://localhost:5000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

export default {
  /** Fetch accounts from DB */
  async getAccounts() {
    const response = await apiClient.get("/teller/get_accounts");
    return response.data;
  },

  /** Refresh accounts from teller link */
  async refreshAccounts() {
    const response = await apiClient.post("/teller/refresh_accounts");
    return response.data;
  },

  async fetchTransactions(page = 1, pageSize = 50) {
    const response = await apiClient.get(
      `/transactions/get_transactions?page=${page}&page_size=${pageSize}`
    );
    return response.data;
  },

  /**
   * Fetch category breakdown data.
   */
  async fetchCategoryBreakdown() {
    const response = await apiClient.get("/charts/category_breakdown");
    return response.data;
  },

  /**
   * Fetch daily net data.
   */
  async fetchDailyNet() {
    const response = await apiClient.get("/charts/daily_net");
    return response.data;
  },

  /**
   * Fetch net assets data.
   */
  async fetchNetAssets() {
    const response = await apiClient.get("/charts/net_assets");
    return response.data;
  },

  /**
   * Update a transaction.
   * Expects a transaction object with at least:
   * { transaction_id, amount, date, description, category, merchant_name, merchant_typ }
   */
  async updateTransaction(transactionData) {
    const response = await apiClient.put("/teller/update_account", transactionData);
    return response.data;
  },
};
