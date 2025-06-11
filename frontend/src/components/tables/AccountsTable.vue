<template>
  <div class="accounts-section">
    <div class="accounts-table">
      <h2>Accounts</h2>

      <!-- Filter Row -->
      <div class="filter-row">
        <input
          v-model="searchQuery"
          class="filter-input"
          type="text"
          placeholder="Filter accounts..."
        />

        <button class="export-btn" @click="controlsVisible = !controlsVisible">
          {{ controlsVisible ? 'Hide Controls' : 'Show Controls' }}
        </button>

        <template v-if="controlsVisible">
          <button class="export-btn" @click="toggleDeleteButtons">
            {{ showDeleteButtons ? 'Hide Delete Buttons' : 'Show Delete Buttons' }}
          </button>

          <button class="export-btn" @click="exportCSV">Export CSV</button>

          <button class="export-btn" @click="showTypeFilter = !showTypeFilter">
            Filter by Type
          </button>

          <button class="export-btn" @click="showHidden = !showHidden">
            {{ showHidden ? 'Hide Hidden' : 'Show Hidden' }}
          </button>
        </template>
      </div>

      <!-- Type Filter Slide -->
      <div class="type-filter-row" :class="{ 'slide-in': showTypeFilter }">
        <select v-model="selectedType" class="filter-input">
          <option value="">All Types</option>
          <option value="checking">Checking</option>
          <option value="savings">Savings</option>
          <option value="credit">Credit</option>
          <option value="loan">Loan</option>
          <option value="investment">Investment</option>
        </select>
      </div>

      <!-- Main Table -->

      <table v-if="!loading && sortedAccounts.length">
        <thead>
          <tr>
            <th @click="sortTable('institution_name')">
              Institution <span>{{ sortKey === 'institution_name' ? (sortOrder === 1 ? '▲' : '▼') : '▲▼' }}</span>
            </th>
            <th @click="sortTable('name')">
              Name <span>{{ sortKey === 'name' ? (sortOrder === 1 ? '▲' : '▼') : '▲▼' }}</span>
            </th>
            <th @click="sortTable('type')">
              Account Type <span>{{ sortKey === 'type' ? (sortOrder === 1 ? '▲' : '▼') : '▲▼' }}</span>
            </th>
            <th @click="sortTable('balance')">
              Balance <span>{{ sortKey === 'balance' ? (sortOrder === 1 ? '▲' : '▼') : '▲▼' }}</span>
            </th>
            <th @click="sortTable('link_type')">
              Link Type <span>{{ sortKey === 'link_type' ? (sortOrder === 1 ? '▲' : '▼') : '▲▼' }}</span>
            </th>
            <th @click="sortTable('last_refreshed')">
              Last Refreshed
              <span>{{ sortKey === 'last_refreshed' ? (sortOrder === 1 ? '▲' : '▼') : '▲▼' }}</span>
            </th>
            <th v-if="controlsVisible">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="account in sortedAccounts" :key="account.account_id">
            <td>{{ account.institution_name || 'N/A' }}</td>
            <td>{{ account.name || 'N/A' }}</td>
            <td>{{ formatType(account.subtype || account.type) }}</td>
            <td>{{ formatBalance(account.balance) }}</td>
            <td>{{ account.link_type || 'N/A' }}</td>
            <td>{{ formatDate(account.last_refreshed) }}</td>
            <td v-if="controlsVisible">
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

      <div v-else-if="!loading && !sortedAccounts.length">
        No accounts found.
      </div>

      <div v-else>
        Loading accounts...
      </div>
    </div>
  </div>
</template>


<script>
import axios from "axios";
import api from "@/services/api";
import accountLinkApi from "@/api/accounts_link";

export default {
  name: "AccountsTable",
  emits: ["refresh"],
  props: {
    provider: {
      type: String,
      default: "teller",
    },
  },
  data() {
    return {
      accounts: [],
      loading: true,
      error: "",
      searchQuery: "",
      sortKey: "",
      sortOrder: 1,
      showDeleteButtons: false,
      showTypeFilter: false,
      selectedType: "",
      typeFilters: [],
      showHidden: false,
      controlsVisible: false,
    };
  },
  computed: {
    uniqueTypes() {
      return [...new Set(this.accounts.map(acc => acc.type).filter(Boolean))];
    },
    filteredAccounts() {
      let results = [...this.accounts];
      if (!this.showHidden) {
        results = results.filter(acc => !acc.is_hidden);
      }
      if (this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase();
        results = results.filter((acc) => {
          const fields = [acc.institution_name, acc.name, acc.type, acc.subtype, acc.status, acc.link_type].map(val => (val || '').toLowerCase());
          return fields.some(f => f.includes(query));
        });
      }
      if (this.selectedType) {
        results = results.filter(acc => acc.type === this.selectedType);
      }
      if (this.typeFilters.length) {
        results = results.filter(acc => this.typeFilters.includes(acc.type));
      }
      return results;
    },
    sortedAccounts() {
      const sorted = [...this.filteredAccounts];
      if (!this.sortKey) return sorted;
      sorted.sort((a, b) => {
        let valA = a[this.sortKey] ?? "";
        let valB = b[this.sortKey] ?? "";
        if (typeof valA === "string") valA = valA.toLowerCase();
        if (typeof valB === "string") valB = valB.toLowerCase();
        if (valA < valB) return -1 * this.sortOrder;
        if (valA > valB) return 1 * this.sortOrder;
        return 0;
      });
      return sorted;
    },
  },
  methods: {
    toggleTypeFilter() {
      this.showTypeFilter = !this.showTypeFilter;
    },
    async fetchAccounts() {
      this.loading = true;
      this.error = "";
      try {
        const response = await axios.get(
          "/api/accounts/get_accounts?include_hidden=true"
        );
        if (response.data?.status === "success") {
          this.accounts = response.data.accounts || [];
        } else {
          this.error = "Error fetching accounts.";
        }
      } catch (err) {
        this.error = err.message || "Error fetching accounts.";
      } finally {
        this.loading = false;
        this.$emit('refresh');
      }
    },
    async deleteAccount(accountId) {
      if (!confirm("Are you sure you want to delete this account and all its transactions?")) return;
      try {
        const res = await accountLinkApi.deleteAccount(this.provider, accountId);
        if (res.status === "success") {
          alert("Account deleted successfully.");
          this.fetchAccounts();
        } else {
          alert("Error deleting account: " + res.message);
        }
      } catch (err) {
        alert("Error: " + err.message);
      }
    },
    async toggleHidden(account) {
      try {
        await api.setAccountHidden(account.account_id, !account.is_hidden);
        this.fetchAccounts();
      } catch (err) {
        alert("Error: " + err.message);
      }
    },
    formatBalance(balance) {
      const number = parseFloat(balance || 0);
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(number);
    },
    formatDate(dateString) {
      if (!dateString) return "N/A";
      return new Date(dateString).toLocaleString();
    },
    formatType(type) {
      if (!type) return 'Unknown';
      return type.charAt(0).toUpperCase() + type.slice(1);
    },
    sortTable(key) {
      if (this.sortKey === key) {
        this.sortOrder = -this.sortOrder;
      } else {
        this.sortKey = key;
        this.sortOrder = 1;
      }
    },
    toggleDeleteButtons() {
      this.showDeleteButtons = !this.showDeleteButtons;
    },
    exportCSV() {
      window.open('/api/export/accounts', '_blank');
    },
  },
  mounted() {
    this.fetchAccounts();
  },
};
</script>


<style scoped>
.accounts-section {
  background-color: var(--color-bg-secondary);
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow);
  color: var(--color-text-light);
}

.accounts-table h2 {
  margin-bottom: 1rem;
  font-size: 1.5rem;
  color: var(--neon-purple);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.filter-input {
  padding: 0.4rem 0.9rem;
  border-radius: 2rem;
  border: 1px solid var(--neon-purple);
  background-color: transparent;
  color: var(--neon-purple);
  font-size: 0.9rem;
  transition: all 0.2s ease-in-out;
}

.filter-input:hover,
.filter-input:focus {
  background-color: var(--neon-purple);
  color: var(--color-bg-dark);
  outline: none;
}

.export-btn {
  background-color: transparent;
  color: var(--neon-purple);
  border: 1px solid var(--neon-purple);
  border-radius: 2rem;
  padding: 0.35rem 0.9rem;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.export-btn:hover {
  background-color: var(--neon-purple);
  color: var(--color-bg-dark);
  border-color: var(--neon-purple);
}

/* Slide-in filter row */
.type-filter-row {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease, margin-top 0.3s ease;
}

.type-filter-row.slide-in {
  max-height: 80px;
  margin-top: 0.5rem;
}

.btn.btn-sm {
  padding: 0.25rem 0.6rem;
  font-size: 0.8rem;
  border: none;
  border-radius: 0.2rem;
  background-color: var(--neon-purple);
  color: var(--);
  cursor: pointer;
  margin-right: 0.25rem;
  transition: background-color 0.2s ease-in-out;
}

.btn.btn-sm:hover {
  background-color: var(--color-accent-purple-hover);
  color: white;
}

.btn-group {
  display: flex;
  gap: 0.25rem;
}

.btn-delete {
  background-color: var(--color-bg-dark);
  color: var(--color-error);
  border: 1px solid var(--color-error);
  border-radius: 2rem;
  padding: 0.35rem 0.9rem;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.btn-delete:hover {
  background-color: var(--color-error);
  color: white;
}

th {
  cursor: pointer;
  user-select: none;
  font-weight: 500;
}

th span {
  margin-left: 0.4rem;
  color: var(--color-text-muted);
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

thead {
  background-color: var(--color-bg-dark);
  color: white;
}

td,
th {
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--divider);
}

tbody tr:hover {
  background-color: var(--hover)-light;
}
</style>
