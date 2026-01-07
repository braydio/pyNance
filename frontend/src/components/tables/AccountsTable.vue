<!-- AccountsTable.vue - Table of linked accounts with filter controls. -->
<template>
  <div class="card table-panel">
    <h2 class="table-title font-bold text-xl mb-6 text-left tracking-wide flex items-center">
      <span class="title-icon i-ph:bank-duotone text-2xl mr-2"></span>
      Accounts
    </h2>
    <!-- Controls/Filters -->
    <div class="control-surface md:p-4" data-testid="accounts-control-bar">
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
        <button
          class="pill md:text-sm"
          :class="{ active: controlsVisible }"
          @click="controlsVisible = !controlsVisible"
        >
          {{ controlsVisible ? 'Hide Options' : 'Show Options' }}
        </button>
        <button
          class="pill md:text-sm"
          :class="{ active: showHidden }"
          @click="showHidden = !showHidden"
        >
          {{ showHidden ? 'Showing Hidden' : 'Hide Hidden' }}
        </button>
        <button
          class="pill md:text-sm"
          :class="{ active: showTypeFilter }"
          @click="showTypeFilter = !showTypeFilter"
        >
          Filter Types
        </button>
        <button
          class="pill md:text-sm"
          :class="{ active: showDeleteButtons }"
          @click="toggleDeleteButtons"
        >
          {{ showDeleteButtons ? 'Delete Visible' : 'Hide Delete' }}
        </button>
        <button class="pill md:text-sm" @click="exportCSV">Export CSV</button>
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
    <div v-if="activeFilters.length" class="filter-tags" data-testid="accounts-filter-tags">
      <span v-for="filter in activeFilters" :key="filter.key" class="filter-tag">
        <span class="filter-tag__label">{{ filter.label }}:</span>
        <span class="filter-tag__value">{{ filter.value }}</span>
        <button type="button" class="filter-tag__remove" @click="removeFilter(filter.key)">
          ×
        </button>
      </span>
    </div>
    <!-- Table -->
    <div class="table-shell">
      <table class="data-table">
        <thead class="table-head">
          <tr>
            <th class="th-cell text-left">Last Refreshed</th>
            <th class="th-cell text-left">Institution</th>
            <th class="th-cell text-left">Name</th>
            <th class="th-cell text-left">Account Type</th>
            <th class="th-cell text-right">Balance</th>
            <th :class="['th-cell text-center', 'w-[60px]']">Trend</th>
            <th v-if="controlsVisible" class="th-cell text-left">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="account in sortedAccounts" :key="account.account_id" class="table-row">
            <!-- Last Refreshed -->
            <td class="cell text-xs cell-muted font-mono">
              {{ formatDate(account.last_refreshed) }}
            </td>
            <!-- Institution with icon -->
            <td class="cell cell-flex">
              <img
                v-if="account.institution_icon_url"
                :src="account.institution_icon_url"
                alt=""
                class="h-5 w-5 rounded-full border border-[var(--divider)] bg-[var(--color-bg)] object-contain"
                loading="lazy"
              />
              <span class="font-medium text-[color:var(--color-accent-blue)]">
                {{ formatTitle(account.institution_name) }}
              </span>
            </td>
            <!-- Name -->
            <td class="cell">{{ formatTitle(account.name) }}</td>
            <!-- Account Type (capitalize first/last) -->
            <td class="cell">
              <span
                :class="[
                  'inline-block rounded-xl border border-[var(--divider)] bg-[var(--color-bg-secondary)]',
                  'px-3 py-1 text-xs font-semibold text-[color:var(--color-accent-blue)]',
                ]"
              >
                {{ capitalizeFirstLast(account.subtype || account.type) }}
              </span>
            </td>
            <!-- Balance -->
            <td class="cell cell-number">
              {{ formatBalance(account.balance) }}
            </td>
            <!-- Sparkline -->
            <td class="cell cell-center">
              <AccountSparkline :account-id="account.account_id" />
            </td>
            <!-- Actions -->
            <td v-if="controlsVisible" class="cell">
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
    <div v-if="!loading && !sortedAccounts.length" class="p-6 text-[color:var(--color-text-muted)]">
      No accounts found.
    </div>
    <div v-else-if="loading" class="p-6 text-[color:var(--color-text-muted)]">
      Loading accounts...
    </div>

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
/**
 * AccountsTable
 *
 * Displays linked accounts with search, visibility, and type filters.
 * Active filters are surfaced as removable tags.
 */
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
          const fields = [acc.institution_name, acc.name, acc.type, acc.subtype, acc.status].map(
            (val) => (val || '').toLowerCase(),
          )
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
    activeFilters() {
      const filters = []
      const query = this.searchQuery.trim()
      if (query) {
        filters.push({ key: 'search', label: 'Search', value: query })
      }
      this.typeFilters.forEach((type) => {
        filters.push({ key: `type:${type}`, label: 'Type', value: this.formatType(type) })
      })
      if (this.showHidden) {
        filters.push({ key: 'hidden', label: 'Hidden', value: 'Included' })
      }
      return filters
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
    /**
     * Remove a single filter tag and reset the associated state.
     * @param {string} key - Filter tag identifier.
     */
    removeFilter(key) {
      if (key === 'search') {
        this.searchQuery = ''
        return
      }
      if (key === 'hidden') {
        this.showHidden = false
        return
      }
      if (key.startsWith('type:')) {
        const type = key.replace('type:', '')
        this.typeFilters = this.typeFilters.filter((entry) => entry !== type)
      }
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
@reference "tailwindcss"; /* Keep Tailwind utilities available for scoped @apply (Tailwind v4) */

.table-panel {
  @apply shadow-xl rounded-2xl p-4 md:p-6;
  background-color: var(--table-surface-strong);
  border: 1px solid var(--table-border);
}

.table-title {
  color: var(--color-accent-blue);
}

.title-icon {
  color: var(--color-accent-blue);
}

.table-shell {
  @apply overflow-x-auto rounded-xl border;
  background-color: var(--table-surface);
  border-color: var(--table-border);
}

.data-table {
  @apply min-w-full text-sm;
  border-collapse: separate;
  border-spacing: 0;
}

.table-head {
  background-color: var(--table-header);
  border-bottom: 1px solid var(--table-border);
}

.th-cell {
  @apply py-2 px-4 text-left font-bold uppercase tracking-wider;
  color: var(--color-text-muted);
  border-right: 1px solid var(--table-border);
}

.th-cell:last-child {
  border-right: none;
}

.table-row {
  background-color: var(--table-surface);
  border-bottom: 1px solid var(--table-border);
  transition: background-color 150ms ease;
}

.table-row:nth-child(even) {
  background-color: var(--table-surface-alt);
}

.table-row:hover {
  background-color: var(--table-hover);
}

.cell {
  @apply px-4 py-2;
  color: var(--text-primary);
}

.cell-muted {
  color: var(--color-text-muted);
}

.cell-flex {
  @apply flex items-center gap-2;
}

.cell-number {
  @apply font-mono text-right font-semibold;
  color: var(--color-accent-blue);
}

.cell-center {
  @apply flex justify-center;
}

.control-surface {
  @apply flex flex-col gap-3 mb-4 rounded-2xl p-3 shadow-inner;
  background-color: var(--table-control);
  border: 1px solid var(--table-border);
}

.input-shell {
  @apply flex items-center gap-3 rounded-xl px-3 py-2;
  background-color: var(--table-surface);
  border: 1px solid var(--table-border);
}

.filter-input {
  @apply flex-1 bg-transparent outline-none;
  color: var(--text-primary);
}

.filter-input::placeholder {
  color: var(--color-text-muted);
}

.filter-input--ghost {
  @apply rounded-xl px-3 py-2 mt-1;
  background-color: var(--table-surface-alt);
  border: 1px solid var(--table-border);
}

.icon {
  @apply text-lg;
  color: var(--color-accent-cyan);
}

.ghost-btn {
  @apply text-xs transition;
  color: var(--color-text-muted);
}

.ghost-btn:hover {
  color: var(--color-accent-blue);
}

.chip-row {
  @apply flex flex-wrap items-center gap-2;
}

.pill {
  @apply text-xs md:text-sm px-3 py-2 rounded-full border transition shadow-sm;
  background-color: var(--table-surface);
  border-color: var(--table-border);
  color: var(--text-primary);
}

.pill.active {
  background-color: var(--table-control);
  border-color: var(--color-accent-blue);
  color: var(--color-accent-blue);
}

.type-filter-row {
  @apply mb-4 rounded-xl p-3 flex flex-col gap-1;
  background-color: var(--table-control);
  border: 1px solid var(--table-border);
}

.type-filter-label {
  @apply text-xs uppercase tracking-wide;
  color: var(--color-text-muted);
}

.filter-tags {
  @apply flex flex-wrap items-center gap-2 mb-4;
}

.filter-tag {
  @apply inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs;
  background-color: color-mix(in srgb, var(--color-accent-blue) 12%, transparent);
  border: 1px solid var(--table-border);
  color: var(--text-primary);
}

.filter-tag__label {
  @apply uppercase tracking-wide text-[11px];
  color: var(--color-accent-blue);
}

.filter-tag__value {
  @apply font-semibold;
}

.filter-tag__remove {
  @apply transition;
  color: var(--color-accent-blue);
}
</style>
