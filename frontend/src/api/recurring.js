
// src/api/recurring.js
import axios from "axios";

export const getRecurringTransactions = async (accountId) => {
  const response = await axios.get(`/api/recurring/${accountId}/recurring`);
  return response.data;
};

export const saveRecurringTransaction = async (accountId, payload) => {
  const response = await axios.put(`/api/recurring/${accountId}/recurringTx`, payload);
  return response.data;
};
