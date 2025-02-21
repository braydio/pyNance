<template>
  <div class="accounts-table">
    <h2>Accounts</h2>
    <!-- Refresh Accounts & Balances -->
    <div class="controls">
      <button @click="fetchAccounts">Refresh Accounts</button>
      <button @click="refreshBalances">Refresh Balances</button>
    </div>
    <!-- Table and other UI elements here -->
    <table v-if="!loading && accounts.length">
      <thead>
        <tr>
          <th>Institution</th>
          <th>Name</th>
          <th>Type</th>
          <th>Balance</th>
          <th>Subtype</th>
          <th>Status</th>
          <th>Link Type</th>
          <th>Last Refreshed</th>
          <th>Account ID</th>
          <th>User ID</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="account in accounts" :key="account.account_id">
          <td>{{ account.institution_name }}</td>
          <td>{{ account.name }}</td>
          <td>{{ account.type }}</td>
          <td>{{ formatBalance(account.balance) }}</td>
          <td>{{ account.subtype }}</td>
          <td>{{ account.status }}</td>
          <td>{{ account.link_type }}</td>
          <td>{{ formatDate(account.last_refreshed) }}</td>
          <td>{{ account.account_id }}</td>
          <td>{{ account.user_id }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="!loading && accounts.length === 0">
      No accounts found.
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "AccountsTable",
  data() {
    return {
      accounts: [],
      loading: false,
      error: ""
    };
  },
  methods: {
    async fetchAccounts() {
      this.loading = true;
      this.error = "";
      try {
        const response = await axios.get('/api/teller/get_accounts');
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
    async refreshBalances() {
      try {
        const response = await axios.post('/api/teller/refresh_balances');
        if (response.data.status === "success") {
          alert("Balances refreshed for accounts: " + response.data.updated_accounts.join(", "));
          // Optionally, re-fetch accounts to update the UI
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
    }
  },
  mounted() {
    this.fetchAccounts();
  }
};
</script>
