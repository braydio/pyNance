<template>
  <div class="link-account">
    <h2>Refresh Teller</h2>
    <div class="button-group">
      <input type="date" v-model="startDate" class="date-picker" />
      <input type="date" v-model="endDate" class="date-picker" />
      <div class="account-select">
        <button type="button" @click="toggleDropdown">Select Accounts</button>
        <div v-if="dropdownOpen" class="dropdown-menu">
          <label v-for="acct in accounts" :key="acct.account_id">
            <input
              type="checkbox"
              :value="acct.account_id"
              v-model="selectedAccounts"
            />
            {{ acct.name }}
          </label>
        </div>
      </div>
      <button @click="handleTellerRefresh" :disabled="isRefreshing">
        <span v-if="isRefreshing">Refreshing Teller Accounts…</span>
        <span v-else>Refresh Teller Accounts</span>
      </button>
    </div>
    <button
      v-if="summaryText"
      class="summary-banner"
      :class="{ error: hasErrors }"
      @click="detailsOpen = !detailsOpen"
    >
      {{ summaryText }}
      <span class="expand-indicator">{{ detailsOpen ? 'Hide' : 'Show' }} details</span>
    </button>

    <div v-if="detailsOpen && refreshResult" class="details-panel">
      <div
        v-for="inst in institutionOrder"
        :key="inst"
        class="institution-block"
      >
        <div class="institution-header">
          <strong>{{ refreshedCountByInstitution[inst] || 0 }}</strong>
          <span>accounts at {{ inst }}</span>
        </div>
        <ul class="accounts-list">
          <li
            v-for="acct in targetedAccountsByInstitution[inst] || []"
            :key="acct.account_id"
            class="account-row"
            :class="{ errored: !!errorByAccountId[acct.account_id] }"
          >
            <button class="account-button" @click="toggleAccountDetails(acct)">
              <span class="account-name">{{ acct.name }}</span>
              <span class="status-pill" :class="errorByAccountId[acct.account_id] ? 'pill-error' : 'pill-ok'">
                {{ errorByAccountId[acct.account_id] ? 'Needs Attention' : 'OK' }}
              </span>
            </button>
            <div v-if="openAccountId === acct.account_id" class="account-details">
              <div v-if="errorByAccountId[acct.account_id]" class="error-details">
                <div class="error-title">{{ errorByAccountId[acct.account_id].plaid_error_message || errorByAccountId[acct.account_id].plaid_error_code }}</div>
                <div class="error-code">Code: {{ errorByAccountId[acct.account_id].plaid_error_code }}</div>
                <div v-if="errorByAccountId[acct.account_id].requires_reauth" class="reauth-hint">
                  Re-authentication required. Use Link update mode to resolve.
                </div>
              </div>
              <div v-else class="tx-list" :class="{ loading: accountDetailsLoading }">
                <div v-if="accountDetailsLoading" class="loading-msg">Loading recent transactions…</div>
                <template v-else>
                  <div v-if="(accountTransactions[acct.account_id] || []).length === 0" class="empty">No transactions in selected range</div>
                  <ul v-else class="tx-scroll">
                    <li v-for="tx in accountTransactions[acct.account_id]" :key="tx.transaction_id" class="tx-item">
                      <span class="tx-date">{{ (tx.date || '').slice(0,10) }}</span>
                      <span class="tx-name">{{ tx.name || tx.description }}</span>
                      <span class="tx-amt">{{ formatAmountDisplay(tx.amount) }}</span>
                    </li>
                  </ul>
                </template>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/services/api";
export default {
  name: "RefreshTellerControls",
  data() {
    const today = new Date().toISOString().slice(0, 10);
    const monthAgo = new Date();
    monthAgo.setDate(monthAgo.getDate() - 30);
    return {
      isRefreshing: false,
      startDate: monthAgo.toISOString().slice(0, 10),
      endDate: today,
      accounts: [],
      selectedAccounts: [],
      dropdownOpen: false,
      message: '',
      messageType: '',
      refreshResult: null,
      detailsOpen: false,
      accountTransactions: {},
      accountDetailsLoading: false,
      openAccountId: null,
    };
  },
  methods: {
    toggleDropdown() {
      this.dropdownOpen = !this.dropdownOpen;
    },
    formatAmountDisplay(val) {
      try {
        const num = typeof val === 'number' ? val : parseFloat(val || 0)
        const sign = num < 0 ? '-' : ''
        return `${sign}$${Math.abs(num).toFixed(2)}`
      } catch {
        return String(val)
      }
    },
    async loadAccounts() {
      try {
        const resp = await api.getAccounts();
        if (resp?.status === "success" && resp.accounts) {
          this.accounts = resp.accounts;
        }
      } catch (err) {
        console.error("Failed to load accounts", err);
        this.message = "Failed to load accounts: " + err.message;
        this.messageType = "error";
      }
    },
    async loadAccountTransactions(accountId) {
      this.accountDetailsLoading = true;
      try {
        const params = {
          start_date: this.startDate,
          end_date: this.endDate,
          limit: 5,
        };
        const res = await api.fetchAccountTransactions(accountId, params);
        const payload = res?.data || res || {};
        const txs = payload.transactions || payload.data?.transactions || [];
        this.accountTransactions = { ...this.accountTransactions, [accountId]: txs };
      } catch (e) {
        console.error('Failed to fetch account transactions', e);
        this.accountTransactions = { ...this.accountTransactions, [accountId]: [] };
      } finally {
        this.accountDetailsLoading = false;
      }
    },
    async toggleAccountDetails(acct) {
      if (this.openAccountId === acct.account_id) {
        this.openAccountId = null;
        return;
      }
      this.openAccountId = acct.account_id;
      if (!this.errorByAccountId[acct.account_id]) {
        await this.loadAccountTransactions(acct.account_id);
      }
    },
    async handleTellerRefresh() {
      this.isRefreshing = true;
      this.refreshResult = null;
      try {
        const response = await api.refreshAccounts({
          start_date: this.startDate,
          end_date: this.endDate,
          account_ids: this.selectedAccounts,
        });
        this.refreshResult = response;
        if (response.status === "success") {
          this.messageType = "success";
          this.detailsOpen = true;
        } else {
          this.message = "Error refreshing Teller accounts: " + response.message;
          this.messageType = "error";
        }
      } catch (err) {
        console.error("Error refreshing Teller accounts:", err);
        this.message = "Error refreshing Teller accounts: " + err.message;
        this.messageType = "error";
      } finally {
        this.isRefreshing = false;
      }
    },
  },
  computed: {
    hasErrors() {
      return !!(this.refreshResult?.errors && this.refreshResult.errors.length)
    },
    refreshedCountByInstitution() {
      return (this.refreshResult?.refreshed_counts) || {}
    },
    totalRefreshedAccounts() {
      const counts = this.refreshedCountByInstitution
      return Object.values(counts).reduce((sum, n) => sum + Number(n || 0), 0)
    },
    totalInstitutions() {
      const counts = this.refreshedCountByInstitution
      return Object.keys(counts).length
    },
    totalErroredAccounts() {
      if (!this.refreshResult || !this.refreshResult.errors) return 0
      return this.refreshResult.errors.reduce((sum, e) => sum + (e.account_ids?.length || 0), 0)
    },
    summaryText() {
      if (!this.refreshResult || this.messageType !== 'success') return this.message
      const accWord = this.totalRefreshedAccounts === 1 ? 'Account' : 'Accounts'
      const instWord = this.totalInstitutions === 1 ? 'Institution' : 'Institutions'
      const base = `Refreshed ${this.totalRefreshedAccounts} ${accWord} at ${this.totalInstitutions} ${instWord}`
      if (this.totalErroredAccounts > 0) {
        const errWord = this.totalErroredAccounts === 1 ? 'Account Needs Attention' : 'Accounts Need Attention'
        return `${base} — ${this.totalErroredAccounts} ${errWord}`
      }
      return base
    },
    errorByAccountId() {
      const map = {}
      const errs = (this.refreshResult?.errors) || []
      for (const e of errs) {
        ;(e.account_ids || []).forEach((id) => {
          map[id] = e
        })
      }
      return map
    },
    targetedAccounts() {
      const ids = this.selectedAccounts?.length ? new Set(this.selectedAccounts) : null
      return (this.accounts || []).filter((a) => (ids ? ids.has(a.account_id) : true))
    },
    targetedAccountsByInstitution() {
      const grouped = {}
      for (const a of this.targetedAccounts) {
        const key = a.institution_name || 'Unknown'
        if (!grouped[key]) grouped[key] = []
        grouped[key].push(a)
      }
      return grouped
    },
    institutionOrder() {
      const countsKeys = Object.keys(this.refreshedCountByInstitution)
      const others = Object.keys(this.targetedAccountsByInstitution).filter(k => !countsKeys.includes(k))
      return [...countsKeys, ...others]
    },
  },
  mounted() {
    this.loadAccounts();
  },
};
</script>

<style scoped>
@reference "../../assets/css/main.css";
.control-block {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px solid var(--color-border-secondary);
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 8px var(--shadow);
  width: 100%;
  max-width: 600px;
}

.control-block h2 {
  margin-bottom: 0.5rem;
  color: var(--color-accent-purple);
  text-align: center;
}

.button-group {
  display: flex;
  justify-content: center;
}

.button-group button {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px solid var(--color-border-secondary);
  border-radius: 3px;
  font-weight: bold;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.button-group button:hover {
  background-color: var(--color-accent-cyan);
  color: var(--themed-bg);
}

.date-picker {
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  background-color: var(--themed-bg);
  border: 1px solid var(--divider);
  color: var(--color-text-light);
}

.account-select {
  position: relative;
}

.account-select button {
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  background-color: var(--themed-bg);
  border: 1px solid var(--divider);
  color: var(--color-text-light);
}

.dropdown-menu {
  position: absolute;
  background-color: var(--themed-bg);
  border: 1px solid var(--divider);
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
}

.summary-banner {
  margin-top: 1rem;
  width: 100%;
  text-align: left;
  background: var(--color-accent-cyan, #06b6d4);
  color: #fff;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}
.summary-banner.error { background: var(--color-error, #e74c3c); }
.expand-indicator { font-weight: 500; opacity: 0.9; }
.details-panel { margin-top: 0.75rem; display: grid; gap: 0.75rem; }
.institution-block { border: 1px solid var(--divider); border-radius: 8px; padding: 0.5rem; }
.institution-header { display: flex; gap: 0.5rem; align-items: baseline; margin-bottom: 0.25rem; }
.accounts-list { display: flex; flex-direction: column; gap: 0.25rem; }
.account-row { border-top: 1px dashed var(--divider); padding-top: 0.25rem; }
.account-row:first-child { border-top: none; }
.account-button { width: 100%; display: flex; justify-content: space-between; align-items: center; background: transparent; border: none; color: inherit; padding: 0.25rem 0.25rem; cursor: pointer; }
.status-pill { padding: 0.1rem 0.5rem; border-radius: 999px; font-size: 0.75rem; }
.pill-ok { background: #e6f9ef; color: #0f5132; }
.pill-error { background: #fde2e1; color: #842029; }
.account-details { margin-top: 0.25rem; }
.error-details { background: #fff5f5; border: 1px solid #fecaca; color: #7f1d1d; border-radius: 6px; padding: 0.5rem; }
.error-title { font-weight: 600; }
.reauth-hint { font-size: 0.85rem; margin-top: 0.25rem; }
.tx-list { border: 1px solid var(--divider); border-radius: 6px; padding: 0.25rem; }
.tx-list.loading { opacity: 0.7; }
.tx-scroll { max-height: 120px; overflow: auto; display: grid; gap: 0.25rem; }
.tx-item { display: grid; grid-template-columns: 5.5rem 1fr auto; gap: 0.5rem; font-size: 0.9rem; }
.tx-date { color: #6b7280; }
.tx-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tx-amt { font-variant-numeric: tabular-nums; }
.empty { color: #6b7280; font-style: italic; padding: 0.25rem; }
</style>
