import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export default {
  async getAccounts(params = {}) {
    const response = await apiClient.get('/accounts/get_accounts', { params })
    return response.data
  },

  async refreshAccounts(payload = {}) {
    const response = await apiClient.post('/accounts/refresh_accounts', payload)
    return response.data
  },

  async fetchAccountTransactions(accountId, params = {}) {
    const response = await apiClient.get(`/transactions/${accountId}/transactions`, { params })
    return response.data
  },

  async getInstitutions() {
    const response = await apiClient.get('/institutions')
    return response.data
  },

  async refreshInstitution(id, payload = {}) {
    const response = await apiClient.post(`/institutions/${id}/refresh`, payload)
    return response.data
  },

  async fetchTransactions(page = 1, pageSize = 50) {
    const response = await apiClient.get(
      `/transactions/get_transactions?page=${page}&page_size=${pageSize}`,
    )
    return response.data
  },

  async fetchCategoryBreakdown(params = {}) {
    const response = await apiClient.get('/charts/category_breakdown', { params })
    return response.data
  },

  async fetchDailyNet() {
    const response = await apiClient.get('/charts/daily_net')
    return response.data
  },

  async fetchCashFlow(params = {}) {
    const response = await apiClient.get('/charts/cash_flow', { params })
    return response.data
  },

  async getAccountSnapshot(params = {}) {
    const response = await apiClient.get('/dashboard/account_snapshot', { params })
    return response.data
  },

  async updateAccountSnapshot(payload = {}) {
    const response = await apiClient.put('/dashboard/account_snapshot', payload)
    return response.data
  },

  async fetchNetAssets() {
    const response = await apiClient.get('/charts/net_assets')
    return response.data
  },

  async updateTransaction(transactionData) {
    const response = await apiClient.put('/transactions/update', transactionData)
    return response.data
  },

  async scanInternalTransfers() {
    const response = await apiClient.post('/transactions/scan-internal')
    return response.data
  },

  async setAccountHidden(account_id, hidden) {
    const response = await apiClient.put(`/accounts/${account_id}/hidden`, { hidden })
    return response.data
  },

  async fetchAccountGroups(params = {}) {
    const response = await apiClient.get('/dashboard/account-groups', { params })
    return response.data
  },

  async createAccountGroup(payload = {}) {
    const response = await apiClient.post('/dashboard/account-groups', payload)
    return response.data
  },

  async updateAccountGroup(groupId, payload = {}) {
    const response = await apiClient.put(`/dashboard/account-groups/${groupId}`, payload)
    return response.data
  },

  async deleteAccountGroup(groupId, payload = {}) {
    const response = await apiClient.delete(`/dashboard/account-groups/${groupId}`, {
      data: payload,
    })
    return response.data
  },

  async reorderAccountGroups(payload = {}) {
    const response = await apiClient.post('/dashboard/account-groups/reorder', payload)
    return response.data
  },

  async setActiveAccountGroup(payload = {}) {
    const response = await apiClient.put('/dashboard/account-groups/active', payload)
    return response.data
  },

  async addAccountToGroup(groupId, payload = {}) {
    const response = await apiClient.post(`/dashboard/account-groups/${groupId}/accounts`, payload)
    return response.data
  },

  async removeAccountFromGroup(groupId, accountId, payload = {}) {
    const response = await apiClient.delete(
      `/dashboard/account-groups/${groupId}/accounts/${accountId}`,
      { data: payload },
    )
    return response.data
  },

  async reorderGroupAccounts(groupId, payload = {}) {
    const response = await apiClient.post(
      `/dashboard/account-groups/${groupId}/accounts/reorder`,
      payload,
    )
    return response.data
  },
}
