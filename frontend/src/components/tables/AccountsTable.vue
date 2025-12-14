<!-- AccountsTable.vue - Table of linked accounts with filter controls. -->
<template>
  <div class="card bg-neutral-950 border border-neutral-800 shadow-xl rounded-2xl p-4 md:p-6">
    <h2 class="font-bold text-xl mb-6 text-left tracking-wide text-blue-300 flex items-center">
      <span class="i-ph:bank-duotone text-2xl mr-2 text-blue-400"></span>
      Accounts
    </h2>
    <!-- Controls/Filters -->
    <div class="control-surface" data-testid="accounts-control-bar">
      <div class="input-shell">
        <span class="icon i-ph:magnifying-glass-duotone"></span>
        <input
          v-model="searchQuery"
          class="filter-input"
          type="text"
          placeholder="Search accounts, institutions, or types"
        />
        <button class="ghost-btn" v-if="searchQuery" @click="searchQuery = ''">Clear</button>
      </div>
      <div class="chip-row">
        <button class="pill" :class="{ active: controlsVisible }" @click="controlsVisible = !controlsVisible">
          {{ controlsVisible ? 'Hide Options' : 'Show Options' }}
        </button>
        <button class="pill" :class="{ active: showHidden }" @click="showHidden = !showHidden">
          {{ showHidden ? 'Showing Hidden' : 'Hide Hidden' }}
        </button>
        <button class="pill" :class="{ active: showTypeFilter }" @click="showTypeFilter = !showTypeFilter">
          Filter Types
        </button>
        <button class="pill" :class="{ active: showDeleteButtons }" @click="toggleDeleteButtons">
          {{ showDeleteButtons ? 'Delete Visible' : 'Hide Delete' }}
        </button>
        <button class="pill" @click="exportCSV">Export CSV</button>
      </div>
    </div>
    <div v-if="showTypeFilter" class="type-filter-row">
      <label class="type-filter-label">Account Types</label>
      <select multiple v-model="typeFilters" class="filter-input filter-input--ghost">
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
              <span class="font-medium text-blue-100">
                {{ formatTitle(account.institution_name) }}
              </span>
            </td>
            <!-- Name -->
            <td class="px-4 py-2 text-blue-50">{{ formatTitle(account.name) }}</td>
            <!-- Account Type (capitalize first/last) -->
            <td class="px-4 py-2">
              <span
                class="inline-block rounded-xl border border-blue-700 bg-gradient-to-r from-neutral-900 to-blue-950 px-3 py-1 text-xs font-semibold text-blue-200"
              >
                {{ capitalizeFirstLast(account.subtype || account.type) }}
              </span>
            </td>
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
                <button v-if="showDeleteButtons" class="btn btn-sm" @click="promptDelete(account)">
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

    <Modal v-if="showDeleteModal" size="md" @close="closeDeleteModal">
      <template #title> Delete account? </template>
      <template #body>
        <p class="text-blue-100">
          This will remove
          <span class="font-semibold">{{ accountPendingDeleteLabel }}</span>
          and all associated transactions. This action cannot be undone.
        </p>
        <div class="mt-6 flex justify-end gap-2">
          <button
            class="btn btn-outline btn-sm"
            type="button"
            :disabled="isDeleting"
            data-testid="delete-modal-cancel"
            @click="closeDeleteModal"
          >
            Cancel
          </button>
          <button
            class="btn btn-error btn-sm"
            type="button"
            :disabled="isDeleting"
            data-testid="delete-modal-confirm"
            @click="confirmDelete"
          >
            {{ isDeleting ? 'Deleting…' : 'Delete' }}
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>

<script>
import api from '@/services/api'
import AccountSparkline from '@/components/widgets/AccountSparkline.vue'
import Modal from '@/components/ui/Modal.vue'
import accountLinkApi from '@/api/accounts_link'
import { useToast } from 'vue-toastification'

export default {
  name: 'AccountsTable',
  components: { AccountSparkline, Modal },
  emits: ['refresh'],
  setup() {
    const toast = useToast()
    return { toast }
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
      showDeleteModal: false,
      accountPendingDelete: null,
      isDeleting: false,
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
    accountPendingDeleteLabel() {
      if (!this.accountPendingDelete) {
        return 'this account'
      }
      const { name, institution_name: institutionName } = this.accountPendingDelete
      return name || institutionName || 'this account'
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
    /**
     * Open the delete confirmation modal for the selected account.
     * @param {object} account - The account slated for deletion.
     */
    promptDelete(account) {
      this.accountPendingDelete = account
      this.showDeleteModal = true
    },
    /**
     * Reset modal state when the user cancels deletion.
     */
    closeDeleteModal() {
      this.showDeleteModal = false
      this.accountPendingDelete = null
    },
    /**
     * Execute the delete API request and surface toast feedback.
     */
    async confirmDelete() {
      if (!this.accountPendingDelete || this.isDeleting) {
        return
      }

      this.isDeleting = true
      try {
        const response = await accountLinkApi.deleteAccount(this.accountPendingDelete.account_id)

        if (response.status === 'success') {
          this.toast.success('Account deleted successfully.')
          this.closeDeleteModal()
          await this.fetchAccounts()
        } else {
          const errorMessage = response.message
            ? `Error deleting account: ${response.message}`
            : 'Error deleting account.'
          this.toast.error(errorMessage)
        }
      } catch (error) {
        const message = error?.message ? `Error: ${error.message}` : 'Error deleting account.'
        this.toast.error(message)
      } finally {
        this.isDeleting = false
        if (!this.showDeleteModal) {
          this.accountPendingDelete = null
        }
      }
    },
    /**
     * Toggle the hidden flag for the provided account and refresh data.
     * @param {object} account - The account whose visibility should change.
     */
    async toggleHidden(account) {
      try {
        await api.setAccountHidden(account.account_id, !account.is_hidden)
        this.fetchAccounts()
      } catch (err) {
        const message = err?.message ? `Error: ${err.message}` : 'Error updating account.'
        this.toast.error(message)
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
    formatTitle(value) {
      if (!value) return 'N/A'
      const str = String(value).toLowerCase()
      return str.replace(/(^|[\s/-])([a-z])/g, (_, sep, ch) => `${sep}${ch.toUpperCase()}`)
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
.control-surface {
  @apply flex flex-col gap-3 mb-4 bg-neutral-900/70 border border-neutral-800 rounded-2xl p-3 md:p-4 shadow-inner;
}

.input-shell {
  @apply flex items-center gap-3 bg-neutral-950 border border-neutral-800 rounded-xl px-3 py-2;
}

.filter-input {
  @apply flex-1 bg-transparent outline-none text-blue-50 placeholder:text-neutral-500;
}

.filter-input--ghost {
  @apply border border-neutral-800 bg-neutral-950/70 rounded-xl px-3 py-2 mt-1;
}

.icon {
  @apply text-blue-400 text-lg;
}

.ghost-btn {
  @apply text-xs text-neutral-400 hover:text-blue-200 transition;
}

.chip-row {
  @apply flex flex-wrap items-center gap-2;
}

.pill {
  @apply text-xs md:text-sm px-3 py-2 rounded-full border border-neutral-700 text-neutral-200 bg-neutral-950/70 hover:border-blue-500 hover:text-blue-200 transition shadow-sm;
}

.pill.active {
  @apply border-blue-500 text-blue-200 bg-blue-950/50;
}

.type-filter-row {
  @apply mb-4 bg-neutral-900/70 border border-neutral-800 rounded-xl p-3 flex flex-col gap-1;
}

.type-filter-label {
  @apply text-xs uppercase tracking-wide text-neutral-400;
}
</style>
