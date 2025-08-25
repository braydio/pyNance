<!-- AccountsTable.vue - Table of linked accounts with filter controls. -->
<template>
  <div class="card bg-neutral-950 border border-neutral-800 shadow-xl rounded-2xl p-4 md:p-6">
    <h2 class="font-bold text-xl mb-6 text-left tracking-wide text-blue-300 flex items-center">
      <span class="i-ph:bank-duotone text-2xl mr-2 text-blue-400"></span>
      Accounts
    </h2>
    <!-- Controls/Filters -->
    <div class="mb-4 flex flex-wrap items-center gap-2" data-testid="accounts-control-bar">
      <div class="flex items-center gap-2 flex-wrap flex-1">
        <input
          v-model="searchQuery"
          class="filter-input"
          type="text"
          placeholder="Filter accounts..."
        />
        <button class="btn btn-outline btn-sm" @click="controlsVisible = !controlsVisible">
          {{ controlsVisible ? 'Hide Controls' : 'Show Controls' }}
        </button>
        <template v-if="controlsVisible">
          <button class="btn btn-outline btn-sm" @click="toggleDeleteButtons">
            {{ showDeleteButtons ? 'Hide Delete Buttons' : 'Show Delete Buttons' }}
          </button>
          <button class="btn btn-outline btn-sm" @click="exportCSV">Export CSV</button>
          <button class="btn btn-outline btn-sm" @click="showTypeFilter = !showTypeFilter">
            Filter by Type
          </button>
          <button class="btn btn-outline btn-sm" @click="showHidden = !showHidden">
            {{ showHidden ? 'Hide Hidden' : 'Show Hidden' }}
          </button>
        </template>
      </div>
      <!-- Maintain width alignment with sparkline column -->
      <div class="flex-none w-[60px]"></div>
    </div>
    <div class="type-filter-row" :class="{ 'slide-in': showTypeFilter }">
      <select multiple v-model="typeFilters" class="filter-input">
        <option v-for="type in uniqueTypes" :key="type" :value="type">
          {{ formatType(type) }}
        </option>
      </select>
    </div>
    <!-- Table -->
    <div class="overflow-x-auto rounded-xl border border-neutral-800">
      <table class="min-w-full text-sm divide-y divide-neutral-800">
        <thead class="bg-neutral-900 border-b border-blue-800">
          <tr>
            <th
              class="py-2 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800"
            >
              Last Refreshed
            </th>
            <th
              class="py-2 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800"
            >
              Institution
            </th>
            <th
              class="py-2 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800"
            >
              Name
            </th>
            <th
              class="py-2 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800"
            >
              Account Type
            </th>
            <th
              class="py-2 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800"
            >
              Link Type
            </th>
            <th
              class="py-2 px-4 text-right font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800"
            >
              Balance
            </th>
            <th
              class="py-2 px-4 text-center font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800 w-[60px]"
            >
              Trend
            </th>
            <th
              v-if="controlsVisible"
              class="py-2 px-4 text-left font-bold uppercase tracking-wider text-blue-200"
            >
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="account in sortedAccounts"
            :key="account.account_id"
            :class="[
              'border-b border-neutral-800',
              'hover:bg-blue-950/50 transition-colors duration-100',
            ]"
          >
            <!-- Last Refreshed -->
            <td class="px-4 py-2 text-xs text-neutral-400">
              {{ formatDate(account.last_refreshed) }}
            </td>
            <!-- Institution with icon -->
            <td class="px-4 py-2 flex items-center gap-2">
              <img
                v-if="account.institution_icon_url"
                :src="account.institution_icon_url"
                alt=""
                class="h-5 w-5 rounded-full border border-neutral-800 bg-neutral-800 object-contain"
                loading="lazy"
              />
              <span class="font-medium text-blue-100">{{ account.institution_name || 'N/A' }}</span>
            </td>
            <!-- Name -->
            <td class="px-4 py-2 text-blue-50">{{ account.name || 'N/A' }}</td>
            <!-- Account Type (capitalize first/last) -->
            <td class="px-4 py-2">
              <span
                class="inline-block rounded-xl border border-blue-700 bg-gradient-to-r from-neutral-900 to-blue-950 px-3 py-1 text-xs font-semibold text-blue-200"
              >
                {{ capitalizeFirstLast(account.subtype || account.type) }}
              </span>
            </td>
            <!-- Link Type -->
            <td class="px-4 py-2 text-blue-200">{{ account.link_type || 'N/A' }}</td>
            <!-- Balance -->
            <td class="px-4 py-2 text-right font-mono font-semibold text-blue-300">
              {{ formatBalance(account.balance) }}
            </td>
            <!-- Sparkline -->
            <td class="px-4 py-2 flex justify-center">
              <AccountSparkline :account-id="account.account_id" />
            </td>
            <!-- Actions -->
            <td v-if="controlsVisible" class="px-4 py-2">
              <div class="btn-group">
                <button class="btn btn-sm" @click="toggleHidden(account)">
                  {{ account.is_hidden ? 'Unhide' : 'Hide' }}
                </button>
                <button
                  v-if="showDeleteButtons"
                  class="btn btn-sm"
                  @click="deleteAccount(account.account_id)"
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="!loading && !sortedAccounts.length" class="p-6 text-blue-200">
      No accounts found.
    </div>
    <div v-else-if="loading" class="p-6 text-blue-200">Loading accounts...</div>
  </div>
</template>

<script>
import api from '@/services/api'
import accountLinkApi from '@/api/accounts_link'
import AccountSparkline from '@/components/widgets/AccountSparkline.vue'

export default {
  name: 'AccountsTable',
  components: { AccountSparkline },
  emits: ['refresh'],
  props: {
    provider: { type: String, default: 'teller' },
  },
  data() {
    return {
      accounts: [],
      loading: true,
      error: '',
      searchQuery: '',
      sortKey: '',
      sortOrder: 1,
      showDeleteButtons: false,
      showTypeFilter: false,
      typeFilters: [],
      showHidden: false,
      controlsVisible: false,
    }
  },
  computed: {
    uniqueTypes() {
      return [...new Set(this.accounts.map((acc) => acc.type).filter(Boolean))]
    },
    filteredAccounts() {
      let results = [...this.accounts]
      if (!this.showHidden) {
        results = results.filter((acc) => !acc.is_hidden)
      }
      if (this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase()
        results = results.filter((acc) => {
          const fields = [
            acc.institution_name,
            acc.name,
            acc.type,
            acc.subtype,
            acc.status,
            acc.link_type,
          ].map((val) => (val || '').toLowerCase())
          return fields.some((f) => f.includes(query))
        })
      }
      if (this.typeFilters.length) {
        results = results.filter((acc) => this.typeFilters.includes(acc.type))
      }
      return results
    },
    sortedAccounts() {
      const sorted = [...this.filteredAccounts]
      if (!this.sortKey) return sorted
      sorted.sort((a, b) => {
        let valA = a[this.sortKey] ?? ''
        let valB = b[this.sortKey] ?? ''
        if (typeof valA === 'string') valA = valA.toLowerCase()
        if (typeof valB === 'string') valB = valB.toLowerCase()
        if (valA < valB) return -1 * this.sortOrder
        if (valA > valB) return 1 * this.sortOrder
        return 0
      })
      return sorted
    },
  },
  methods: {
    toggleTypeFilter() {
      this.showTypeFilter = !this.showTypeFilter
    },
    async fetchAccounts() {
      this.loading = true
      this.error = ''
      try {
        const response = await api.getAccounts({ include_hidden: true })
        if (response.status === 'success') {
          this.accounts = response.accounts || []
        } else {
          this.error = 'Error fetching accounts.'
        }
      } catch (err) {
        this.error = err.message || 'Error fetching accounts.'
      } finally {
        this.loading = false
        this.$emit('refresh')
      }
    },
    async deleteAccount(accountId) {
      if (!confirm('Are you sure you want to delete this account and all its transactions?')) return
      try {
        const res = await accountLinkApi.deleteAccount(this.provider, accountId)
        if (res.status === 'success') {
          alert('Account deleted successfully.')
          this.fetchAccounts()
        } else {
          alert('Error deleting account: ' + res.message)
        }
      } catch (err) {
        alert('Error: ' + err.message)
      }
    },
    async toggleHidden(account) {
      try {
        await api.setAccountHidden(account.account_id, !account.is_hidden)
        this.fetchAccounts()
      } catch (err) {
        alert('Error: ' + err.message)
      }
    },
    formatBalance(balance) {
      const number = parseFloat(balance || 0)
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(number)
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date
        .toLocaleDateString('en-US', {
          year: '2-digit',
          month: 'short',
          day: 'numeric',
        })
        .replace(/,/, '') // Ensures format like 'Jul 16 25'
    },
    formatType(type) {
      if (!type) return 'Unknown'
      return type.charAt(0).toUpperCase() + type.slice(1)
    },
    capitalizeFirstLast(type) {
      if (!type || typeof type !== 'string') return 'Unknown'
      const clean = type.toLowerCase()
      if (clean.length < 2) return clean.toUpperCase()
      return (
        clean.charAt(0).toUpperCase() +
        clean.slice(1, -1) +
        clean.charAt(clean.length - 1).toUpperCase()
      )
    },
    sortTable(key) {
      if (this.sortKey === key) {
        this.sortOrder = -this.sortOrder
      } else {
        this.sortKey = key
        this.sortOrder = 1
      }
    },
    toggleDeleteButtons() {
      this.showDeleteButtons = !this.showDeleteButtons
    },
    exportCSV() {
      window.open('/api/export/accounts', '_blank')
    },
  },
  mounted() {
    this.fetchAccounts()
  },
}
</script>

<style scoped>
/* Use blue analytic styles, card/table borders, and hover/active transitions as above */
</style>
