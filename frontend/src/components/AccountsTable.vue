<template>
  <div class="accounts-section">
    <div class="accounts-table">
      <h2>Accounts</h2>

      <!-- Filter & Controls Row -->
      <div class="filter-row">
        <input
          v-model="searchQuery"
          class="filter-input"
          type="text"
          placeholder="Filter accounts..."
        />
        <!-- Use the new RefreshControls component -->
        <RefreshControls :onFetch="fetchAccounts" :onRefresh="refreshAccounts" />
      </div>

      <!-- Table -->
      <table v-if="!loading && sortedAccounts.length">
        <thead>
          <tr>
            <th @click="sortTable('institution_name')">
              Institution
              <span v-if="sortKey === 'institution_name'">
                {{ sortOrder === 1 ? '▲' : '▼' }}
              </span>
            </th>
            <th @click="sortTable('name')">
              Name
              <span v-if="sortKey === 'name'">
                {{ sortOrder === 1 ? '▲' : '▼' }}
              </span>
            </th>
            <th @click="sortTable('type')">
              Type
              <span v-if="sortKey === 'type'">
                {{ sortOrder === 1 ? '▲' : '▼' }}
              </span>
            </th>
            <th @click="sortTable('balance')">
              Balance
              <span v-if="sortKey === 'balance'">
                {{ sortOrder === 1 ? '▲' : '▼' }}
              </span>
            </th>
            <th @click="sortTable('subtype')">
              Subtype
              <span v-if="sortKey === 'subtype'">
                {{ sortOrder === 1 ? '▲' : '▼' }}
              </span>
            </th>
            <th @click="sortTable('status')">
              Status
              <span v-if="sortKey === 'status'">
                {{ sortOrder === 1 ? '▲' : '▼' }}
              </span>
            </th>
            <th @click="sortTable('link_type')">
              Link Type
              <span v-if="sortKey === 'link_type'">
                {{ sortOrder === 1 ? '▲' : '▼' }}
              </span>
            </th>
            <th @click="sortTable('last_refreshed')">
              Last Refreshed
              <span v-if="sortKey === 'last_refreshed'">
                {{ sortOrder === 1 ? '▲' : '▼' }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="account in sortedAccounts" :key="account.account_id">
            <td>{{ account.institution_name }}</td>
            <td>{{ account.name }}</td>
            <td>{{ account.type }}</td>
            <td>{{ formatBalance(account.balance) }}</td>
            <td>{{ account.subtype }}</td>
            <td>{{ account.status }}</td>
            <td>{{ account.link_type }}</td>
            <td>{{ formatDate(account.last_refreshed) }}</td>
          </tr>
        </tbody>
      </table>

      <div v-if="!loading && sortedAccounts.length === 0">
        No accounts found.
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import RefreshControls from "@/components/RefreshControls.vue";

export default {
  name: "AccountsTable",
  components: { RefreshControls },
  data() {
    return {
      accounts: [],
      loading: false,
      error: "",
      searchQuery: "",
      sortKey: "",
      sortOrder: 1,
    };
  },
  computed: {
    filteredAccounts() {
      if (!this.searchQuery.trim()) {
        return this.accounts;
      }
      const query = this.searchQuery.toLowerCase();
      return this.accounts.filter((acc) => {
        const fieldsToSearch = [
          acc.institution_name,
          acc.name,
          acc.type,
          acc.subtype,
          acc.status,
          acc.link_type,
        ].map((val) => (val || "").toString().toLowerCase());
        return fieldsToSearch.some((field) => field.includes(query));
      });
    },
    sortedAccounts() {
      const sorted = [...this.filteredAccounts];
      if (!this.sortKey) {
        return sorted;
      }
      sorted.sort((a, b) => {
        let valA = a[this.sortKey];
        let valB = b[this.sortKey];
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
    async fetchAccounts() {
      this.loading = true;
      this.error = "";
      try {
        const response = await axios.get("/api/teller/transactions/get_accounts");
        if (response.data && response.data.status === "success") {
          this.accounts = response.data.data.accounts;
        } else {
          this.error = "Error fetching accounts.";
        }
      } catch (err) {
        this.error = err.message || "Error fetching accounts.";
      } finally {
        this.loading = false;
      }
    },
    async refreshAccounts() {
      try {
        const response = await axios.post("/api/teller/transactions/refresh_balances");
        if (response.data.status === "success") {
          const accountNames = response.data.updated_accounts.map(
            (acc) => acc.account_name
          );
          alert("Balances refreshed for: " + accountNames.join(", "));
          // Optionally, re-fetch accounts after refresh.
          this.fetchAccounts();
        } else {
          alert("Failed to refresh balances: " + response.data.message);
        }
      } catch (err) {
        console.error("Error refreshing balances:", err);
        alert("Error refreshing balances: " + err.message);
      }
    },
    formatBalance(balance) {
      const number = parseFloat(balance);
      const formatter = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        currencySign: "accounting",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      return formatter.format(number);
    },
    formatDate(dateString) {
      if (!dateString) return "";
      const dateObj = new Date(dateString);
      return dateObj.toLocaleString();
    },
    sortTable(key) {
      if (this.sortKey === key) {
        this.sortOrder = -this.sortOrder;
      } else {
        this.sortKey = key;
        this.sortOrder = 1;
      }
    },
  },
  mounted() {
    this.fetchAccounts();
  },
};
</script>

<style>
:root {
  --gruvbox-bg: #282828;
  --gruvbox-fg: #ebdbb2;
  --gruvbox-yl: #fabd2f;
  --gruvbox-accent: #d65d0e;
  --gruvbox-hover: #b0520c;
  --gruvbox-border: #3c3836;
  --gruvbox-hover-bg: #32302f;
}

.accounts-table {
  background-color: var(--gruvbox-bg);
  color: var(--gruvbox-fg);
  padding: 1rem;
  border: 1px solid var(--gruvbox-border);
  border-radius: 4px;
}
.accounts-table h2 {
  margin-top: 0;
  color: var(--gruvbox-yl);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}
.filter-input {
  flex: 1;
  padding: 0.4rem 0.6rem;
  border: 1px solid var(--gruvbox-border);
  border-radius: 4px;
  background-color: #1d2021;
  color: var(--gruvbox-fg);
  outline: none;
}
.filter-input:focus {
  border-color: var(--gruvbox-yl);
}
</style>
