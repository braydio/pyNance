<template>
  <Card class="space-y-4">
    <h2 class="text-lg font-semibold text-center">Refresh Plaid</h2>
    <div class="flex flex-wrap gap-3">
      <input type="date" v-model="startDate" class="input" />
      <input type="date" v-model="endDate" class="input" />
      <div class="account-select" v-click-outside="closeDropdown">
        <UiButton type="button" variant="outline" @click="toggleDropdown">All Linked Accounts</UiButton>
        <div v-if="dropdownOpen" class="dropdown-menu">
          <label v-for="acct in accounts" :key="acct.account_id">
            <input type="checkbox" :value="acct.account_id" v-model="selectedAccounts" />
            {{ acct.name }}
          </label>
        </div>
      </div>
      <UiButton
        type="button"
        variant="primary"
        @click="handlePlaidRefresh"
        :disabled="isRefreshing"
      >
        <span v-if="isRefreshing">Syncing Account Activity…</span>
        <span v-else>Sync Account Activity</span>
      </UiButton>
    </div>
    <UiButton
      v-if="summaryText"
      class="w-full justify-between"
      :variant="hasErrors ? 'alert' : 'primary'"
      type="button"
      @click="detailsOpen = !detailsOpen"
    >
      {{ summaryText }}
      <span class="text-sm font-medium opacity-80"
        >{{ detailsOpen ? 'Hide' : 'Show' }} details</span
      >
    </UiButton>

    <div v-if="detailsOpen && refreshResult" class="details-panel">
      <div v-for="inst in institutionOrder" :key="inst" class="institution-block">
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
              <span
                class="status-pill"
                :class="errorByAccountId[acct.account_id] ? 'pill-error' : 'pill-ok'"
              >
                {{ errorByAccountId[acct.account_id] ? 'Needs Attention' : 'OK' }}
              </span>
            </button>
            <div v-if="openAccountId === acct.account_id" class="account-details">
              <div v-if="errorByAccountId[acct.account_id]" class="error-details">
                <div class="error-title">
                  {{
                    errorByAccountId[acct.account_id].plaid_error_message ||
                    errorByAccountId[acct.account_id].plaid_error_code
                  }}
                </div>
                <div class="error-code">
                  Code: {{ errorByAccountId[acct.account_id].plaid_error_code }}
                </div>
                <div v-if="errorByAccountId[acct.account_id].requires_reauth" class="reauth-hint">
                  Re-authentication required. Use Link update mode to resolve.
                </div>
              </div>
              <div v-else class="tx-list" :class="{ loading: accountDetailsLoading }">
                <div v-if="accountDetailsLoading" class="loading-msg">
                  Loading recent transactions…
                </div>
                <template v-else>
                  <div
                    v-if="(accountTransactions[acct.account_id] || []).length === 0"
                    class="empty"
                  >
                    No transactions in selected range
                  </div>
                  <ul v-else class="tx-scroll">
                    <li
                      v-for="tx in accountTransactions[acct.account_id]"
                      :key="tx.transaction_id"
                      class="tx-item"
                    >
                      <span class="tx-date">{{ (tx.date || '').slice(0, 10) }}</span>
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
  </Card>
</template>

<script>
import Card from '@/components/ui/Card.vue'
import UiButton from '@/components/ui/Button.vue'
import api from '@/services/api'
export default {
  name: 'RefreshPlaidControls',
  components: {
    Card,
    UiButton,
  },
  data() {
    const today = new Date().toISOString().slice(0, 10)
    const monthAgo = new Date()
    monthAgo.setDate(monthAgo.getDate() - 30)
    return {
      isRefreshing: false,
      user_id: import.meta.env.VITE_USER_ID_PLAID,
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
    }
  },
  methods: {
    toggleDropdown() {
      this.dropdownOpen = !this.dropdownOpen
    },
    closeDropdown() {
      this.dropdownOpen = false
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
        const resp = await api.getAccounts()
        if (resp?.status === 'success' && resp.accounts) {
          this.accounts = resp.accounts
        } else {
          this.accounts = []
          this.message = 'Error fetching accounts.'
          this.messageType = 'error'
        }
      } catch (err) {
        console.error('Failed to load accounts', err)
        this.message = 'Failed to load accounts: ' + err.message
        this.messageType = 'error'
      }
    },
    async loadAccountTransactions(accountId) {
      this.accountDetailsLoading = true
      try {
        const params = {
          start_date: this.startDate,
          end_date: this.endDate,
          limit: 5,
        }
        const res = await api.fetchAccountTransactions(accountId, params)
        const payload = res?.data || res || {}
        const txs = payload.transactions || payload.data?.transactions || []
        this.accountTransactions = { ...this.accountTransactions, [accountId]: txs }
      } catch (e) {
        console.error('Failed to fetch account transactions', e)
        this.accountTransactions = { ...this.accountTransactions, [accountId]: [] }
      } finally {
        this.accountDetailsLoading = false
      }
    },
    async toggleAccountDetails(acct) {
      if (this.openAccountId === acct.account_id) {
        this.openAccountId = null
        return
      }
      this.openAccountId = acct.account_id
      if (!this.errorByAccountId[acct.account_id]) {
        await this.loadAccountTransactions(acct.account_id)
      }
    },
    async handlePlaidRefresh() {
      this.dropdownOpen = false
      this.isRefreshing = true
      this.refreshResult = null
      try {
        const response = await api.refreshAccounts({
          user_id: this.user_id,
          start_date: this.startDate,
          end_date: this.endDate,
          account_ids: this.selectedAccounts,
        })
        this.refreshResult = response
        if (response.status === 'success') {
          this.messageType = 'success'
          this.detailsOpen = true
        } else {
          this.message = 'Error refreshing Plaid accounts: ' + response.message
          this.messageType = 'error'
        }
      } catch (err) {
        console.error('Error refreshing Plaid accounts:', err)
        this.message = 'Error refreshing Plaid accounts: ' + err.message
        this.messageType = 'error'
      } finally {
        this.isRefreshing = false
      }
    },
  },
  computed: {
    hasErrors() {
      return !!(this.refreshResult?.errors && this.refreshResult.errors.length)
    },
    refreshedCountByInstitution() {
      return this.refreshResult?.refreshed_counts || {}
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
        const errWord =
          this.totalErroredAccounts === 1 ? 'Account Needs Attention' : 'Accounts Need Attention'
        return `${base} — ${this.totalErroredAccounts} ${errWord}`
      }
      return base
    },
    errorByAccountId() {
      const map = {}
      const errs = this.refreshResult?.errors || []
      for (const e of errs) {
        ;(e.account_ids || []).forEach((id) => {
          map[id] = e
        })
      }
      return map
    },
    targetedAccounts() {
      const ids = this.selectedAccounts?.length ? new Set(this.selectedAccounts) : null
      return (this.accounts ?? []).filter((account) => ids?.has(account.account_id) ?? true)
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
      // Order by refreshed_counts keys first, then any others
      const countsKeys = Object.keys(this.refreshedCountByInstitution)
      const others = Object.keys(this.targetedAccountsByInstitution).filter(
        (k) => !countsKeys.includes(k),
      )
      return [...countsKeys, ...others]
    },
  },
  mounted() {
    this.loadAccounts()
  },
}
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

.account-select {
  position: relative;
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
.success-badge,
.error-badge {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: bold;
  color: #fff;
}
.success-badge {
  background-color: var(--color-bg-success, #2ecc71);
}
.error-badge {
  background-color: var(--color-error, #e74c3c);
}

.details-panel {
  margin-top: 0.75rem;
  display: grid;
  gap: 0.75rem;
}
.institution-block {
  border: 1px solid var(--divider);
  border-radius: 8px;
  padding: 0.5rem;
}
.institution-header {
  display: flex;
  gap: 0.5rem;
  align-items: baseline;
  margin-bottom: 0.25rem;
}
.accounts-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.account-row {
  border-top: 1px dashed var(--divider);
  padding-top: 0.25rem;
}
.account-row:first-child {
  border-top: none;
}
.account-button {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: transparent;
  border: none;
  color: inherit;
  padding: 0.25rem 0.25rem;
  cursor: pointer;
}
.status-pill {
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  font-size: 0.75rem;
}
.pill-ok {
  background: #e6f9ef;
  color: #0f5132;
}
.pill-error {
  background: #fde2e1;
  color: #842029;
}
.account-details {
  margin-top: 0.25rem;
}
.error-details {
  background: #fff5f5;
  border: 1px solid #fecaca;
  color: #7f1d1d;
  border-radius: 6px;
  padding: 0.5rem;
}
.error-title {
  font-weight: 600;
}
.reauth-hint {
  font-size: 0.85rem;
  margin-top: 0.25rem;
}
.tx-list {
  border: 1px solid var(--divider);
  border-radius: 6px;
  padding: 0.25rem;
}
.tx-list.loading {
  opacity: 0.7;
}
.tx-scroll {
  max-height: 120px;
  overflow: auto;
  display: grid;
  gap: 0.25rem;
}
.tx-item {
  display: grid;
  grid-template-columns: 5.5rem 1fr auto;
  gap: 0.5rem;
  font-size: 0.9rem;
}
.tx-date {
  color: #6b7280;
}
.tx-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tx-amt {
  font-variant-numeric: tabular-nums;
}
.empty {
  color: #6b7280;
  font-style: italic;
  padding: 0.25rem;
}
</style>
