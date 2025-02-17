// src/services/api.js
import axios from "axios";

// Create an Axios instance; adjust the base URL as needed.
const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || "http://localhost:5000/api",
  headers: {
    "Content-Type": "application/json"
  }
});

export default {
  /**
   * Fetch transactions with pagination.
   * @param {number} page - Current page.
   * @param {number} pageSize - Number of transactions per page.
   */
  async fetchTransactions(page = 1, pageSize = 50) {
    const response = await apiClient.get(`/transactions/?page=${page}&page_size=${pageSize}`);
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
   * Fetch cash flow data.
   * @param {string} granularity - "monthly" or "daily"
   */
  async fetchCashFlow(granularity = "monthly") {
    const url =
      granularity === "daily"
        ? "/charts/cash_flow?granularity=daily"
        : "/charts/cash_flow";
    const response = await apiClient.get(url);
    return response.data;
  },

  /**
   * Fetch net assets data.
   */
  async fetchNetAssets() {
    const response = await apiClient.get("/charts/net_assets");
    return response.data;
  }
};
