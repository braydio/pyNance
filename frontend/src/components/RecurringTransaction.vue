
<template>
  <div class="recurring-transactions-section">
    <!-- Section to display available accounts (fetched from API) -->
    <div class="accounts-dropdown" v-if="accounts.length">
      <label for="accountSelect">Select Account:</label>
      <select id="accountSelect" v-model="selectedAccountId">
        <option disabled value="">-- choose an account --</option>
        <option
          v-for="acc in accounts"
          :key="acc.account_id"
          :value="acc.account_id"
        >
          {{ acc.name }} ({{ acc.type || 'Unknown Type' }})
        </option>
      </select>
    </div>

    <!-- Display any notifications for the currently selected account -->
    <div class="notifications-container" v-if="notifications.length">
      <h3>Upcoming Recurring Transactions</h3>
      <p
        v-for="(notif, idx) in notifications"
        :key="idx"
        class="notification-message"
      >
        {{ notif }}
      </p>
    </div>

    <!-- Manual Recurring Transaction Form -->
    <div class="manual-recurring-section">
      <label for="manualAmount">Set Recurring Transaction ($):</label>
      <input
        id="manualAmount"
        v-model.number="txAmount"
        type="number"
        step="0.01"
      />
      <button @click="saveRecurring">Save</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import api from '@/services/api';

export default {
  name: "RecurringTransaction",
  data() {
    return {
      accounts: [],
      selectedAccountId: "",
      notifications: [],
      txAmount: 0,
    };
  },
  watch: {
    // Whenever user changes the selected account, fetch that account's recurring transactions
    selectedAccountId(newVal) {
      if (newVal) {
        this.fetchRecurringTransactions(newVal);
      } else {
        this.notifications = [];
      }
    },
  },
  methods: {
    // 1. Fetch Accounts (reference method from provided snippet)
    async fetchAccounts() {
      try {
        const response = await axios.get("/api/teller/transactions/get_accounts");
        if (response.data && response.data.status === "success") {
          // response.data.data.accounts or response.data.data can hold the list
          const fetched = response.data.data.accounts || response.data.data || [];
          this.accounts = fetched;
          // Optionally, pick a default (e.g., first account):
          if (this.accounts.length) {
            this.selectedAccountId = this.accounts[0].account_id;
          }
        } else {
          console.error("Error fetching accounts:", response.data);
        }
      } catch (err) {
        console.error("Error fetching accounts:", err);
      }
    },

    // 2. Fetch recurring transactions for the selected account
    async fetchRecurringTransactions(accountId) {
      if (!accountId) {
        console.warn("No account ID selected. Skipping fetch of recurring transactions.");
        return;
      }
      try {
        // Example usage: GET /api/accounts/:account_id/recurring
        const resp = await api.get(`/accounts/${accountId}/recurring`);
        if (resp.status === 'success') {
          this.notifications = resp.reminders;
        } else {
          console.warn('Failed to fetch recurring transactions:', resp);
          this.notifications = [];
        }
      } catch (err) {
        console.error('Error fetching recurring transactions:', err);
        this.notifications = [];
      }
    },

    // 3. Save (create/update) a recurring transaction
    async saveRecurring() {
      if (!this.selectedAccountId) {
        console.error("No account selected. Cannot save recurring transaction.");
        return;
      }
      try {
        // Example usage: PUT /api/accounts/:account_id/recurringTx
        const resp = await api.put(`/accounts/${this.selectedAccountId}/recurringTx`, {
          amount: this.txAmount,
        });
        console.log('Recurring transaction saved:', resp);
        // Re-fetch recurring transactions to refresh the notifications list
        await this.fetchRecurringTransactions(this.selectedAccountId);
      } catch (err) {
        console.error('Error saving recurring transaction:', err);
      }
    },
  },
  async mounted() {
    // Fetch accounts when component mounts
    await this.fetchAccounts();
  },
};
</script>

<style scoped>
@import '@/styles/global-colors.css';

.recurring-transactions-section {
  padding: 1rem;
  background-color: var(--gruvbox-bg, #282828);
  border-radius: 8px;
  color: var(--gruvbox-fg, #ebdbb2);
  font-family: "Fira Code", monospace;
}

/* Accounts Dropdown */
.accounts-dropdown {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.accounts-dropdown select {
  padding: 0.4rem;
  border-radius: 4px;
  border: 1px solid var(--gruvbox-border, #3c3836);
  background-color: #1d2021;
  color: var(--gruvbox-fg, #ebdbb2);
}

/* Notifications Container */
.notifications-container {
  background-color: var(--page-bg, #1d2021);
  color: var(--gruvbox-fg, #ebdbb2);
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.notification-message {
  margin: 0.25rem 0;
  font-size: 0.9rem;
}

/* Manual Recurring Form */
.manual-recurring-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.manual-recurring-section input {
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid var(--gruvbox-border, #3c3836);
  background-color: #1d2021;
  color: var(--gruvbox-fg, #ebdbb2);
}

.manual-recurring-section button {
  align-self: flex-start;
  background-color: var(--gruvbox-accent, #d3869b);
  color: var(--gruvbox-fg, #ebdbb2);
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.manual-recurring-section button:hover {
  background-color: var(--gruvbox-hover, #504945);
}
</style>

