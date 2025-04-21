<style scoped>
@import '@/styles/global-colors.css';
</style>

<template>
  <div class="accounts-section">
    <div class="accounts-table">
      <h2>Accounts</h2>

      <!-- Filter & Controls Row -->
      <div class="filter-row">
        <input v-model="searchQuery" class="filter-input" type="text" placeholder="Filter accounts..." />

        <button class="theme-buttons-top" @click="toggleDeleteButtons">
          {{ showDeleteButtons ? "Hide Delete Buttons" : "Show Delete Buttons" }}
        </button>

        <!-- CSV Export/Import Buttons -->
        <button class="theme-buttons-top" @click="exportCSV">Export CSV</button>
      </div>

      <!-- Table -->
      <table v-if="!loading && sortedAccounts.length">
        <thead>
          <tr>
            <th @click="sortTable('institution_name')">
              Institution
              <span>
                <template v-if="sortKey === 'institution_name'">
                  {{ sortOrder === 1 ? '▲' : '▼' }}
                </template>
                <template v-else>▲▼</template>
              </span>
            </th>
            <th @click="sortTable('name')">
              Name
              <span>
                <template v-if="sortKey === 'name'">
                  {{ sortOrder === 1 ? '▲' : '▼' }}
                </template>
                <template v-else>▲▼</template>
              </span>
            </th>
            <th @click="sortTable('type')">
              Type
              <span>
                <template v-if="sortKey === 'type'">
                  {{ sortOrder === 1 ? '▲' : '▼' }}
                </template>
                <template v-else>▲▼</template>
              </span>
            </th>
            <th @click="sortTable('balance')">
              Balance
              <span>
                <template v-if="sortKey === 'balance'">
                  {{ sortOrder === 1 ? '▲' : '▼' }}
                </template>
                <template v-else>▲▼</template>
              </span>
            </th>
            <th @click="sortTable('subtype')">
              Subtype
              <span>
                <template v-if="sortKey === 'subtype'">
                  {{ sortOrder === 1 ? '▲' : '▼' }}
                </template>
                <template v-else>▲▼</template>
              </span>
            </th>
            <th @click="sortTable('link_type')">
              Link Type
              <span>
                <template v-if="sortKey === 'link_type'">
                  {{ sortOrder === 1 ? '▲' : '▼' }}
                </template>
                <template v-else>▲▼</template>
              </span>
            </th>
            <th @click="sortTable('last_refreshed')">
              Last Refreshed
              <span>
                <template v-if="sortKey === 'last_refreshed'">
                  {{ sortOrder === 1 ? '▲' : '▼' }}
                </template>
                <template v-else>▲▼</template>
              </span>
            </th>
            <th v-if="showDeleteButtons">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="account in sortedAccounts" :key="account.account_id">
            <td>{{ account.institution_name }}</td>
            <td>{{ account.name }}</td>
            <td>{{ account.type }}</td>
            <td>{{ formatBalance(account.balance) }}</td>
            <td>{{ account.subtype }}</td>
            <td>{{ account.link_type }}</td>
            <td>{{ formatDate(account.last_refreshed) }}</td>
            <td v-if="showDeleteButtons">
              <button class="delete-btn" @click="deleteAccount(account.account_id)">Delete</button>
            </td>
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
import api from "@/services/api"; // Ensure the API service is imported
import RefreshControls from "@/components/RefreshControls.vue";


export default {
  name: "AccountsTable",
  components: { RefreshControls },
  props: {
    provider: {
      type: String,
      default: "teller",
    },
  },
  data() {
    return {
      accounts: [],
      loading: false,
      error: "",
      searchQuery: "",
      sortKey: "",
      sortOrder: 1,
      showDeleteButtons: false, // controls the visibility of delete buttons
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
        let response = await axios.get("/api/accounts/get_accounts");
        console.log("API response:", response.data); // <--- ADD THIS
        if (response.data && response.data.status === "success") {
          this.accounts = response.data.accounts;
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
        let response;
        if (this.provider === "plaid") {
          response = await axios.post("/api/plaid/transactions/refresh_accounts");
        } else {
          response = await axios.post("/api/teller/transactions/refresh_balances");
        }
        if (response.data.status === "success") {
          const accountNames = response.data.updated_accounts.map(
            (acc) => acc.account_name
          );
          alert("Balances refreshed for: " + accountNames.join(", "));
          this.fetchAccounts();
        } else {
          alert("Failed to refresh balances: " + response.data.message);
        }
      } catch (err) {
        console.error("Error refreshing balances:", err);
        alert("Error refreshing balances: " + err.message);
      }
    },
    async deleteAccount(account) {
      if (!confirm("Are you sure you want to delete this account and all its transactions?")) return;

      try {
        const res = await api.deleteAccount(account.link_type || "plaid", account.account_id);
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
    formatBalance(balance) {
      const number = parseFloat(balance);
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        currencySign: "accounting",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(number);
    },
    formatDate(dateString) {
      if (!dateString) return "";
      return new Date(dateString).toLocaleString();
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
  },
  mounted() {
    this.fetchAccounts();
  },
};
</script>
<style>
/* Accounts Table Container */
.accounts-table {
  background-color: var(--background);
  color: var(--foreground);
  padding: 0.5rem;
  border: 1px solid var(--border);
  border-radius: 4px;
}

/* <-- Added closing bracket here */

/* Heading */
.accounts-table h2 {
  margin-top: 0;
  color: var(--accent);
  font-family: "Fira Code", monospace;
  font-size: 1.5rem;
}

/* Filter Row */
.filter-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

/* Filter Input */
.filter-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background-color: var(--hover);
  color: var(--foreground);
  font-family: "Fira Code", monospace;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s ease;
}

.filter-input:focus {
  border-color: var(--hover);
}

/* Toggle Delete Buttons Button */
.theme-buttons-top {
  padding: 0.5rem 1rem;
  background-color: var(--background);
  color: var(--foreground);
  border: 1px groove var(--background);
  border-radius: 0px;
  cursor: pointer;
  font-family: "Fira Code", monospace;
  font-weight: bold;
}

.theme-buttons-top:hover {
  color: var(--foreground);
  background-color: var(--hover);
  border: 1px groove transparent;
}

/* Table Styling */
table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 0.75rem 1rem;
  border: 1px solid var(--border);
  text-align: left;
  font-family: "Fira Code", monospace;
  font-size: 0.9rem;
}

th {
  cursor: pointer;
  background-color: var(--input-bg);
  color: var(--foreground);
  position: relative;
}

th span {
  margin-left: 0.5rem;
  font-size: 0.8rem;
  opacity: 0.8;
}

/* Delete Button Styling */


.delete-btn {
  padding: 0.4rem 0.8rem;
  background-color: var(--error);
  color: #ffffff;
  border: 1px solid var(--error);
  border-radius: 4px;
  cursor: pointer;
  font-family: "Fira Code", monospace;
  font-weight: bold;
  transition: background-color 0.2s ease, transform 0.2s ease;
}

.delete-btn:hover {
  background-color: #ff6666;
  transform: translateY(-1px);
}

/* Table Row Hover Effect */
tbody tr:hover {
  background-color: var(--hover);
}
</style>
