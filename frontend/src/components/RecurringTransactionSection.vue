<template>
    <div class="recurring-transactions-section">

      <!-- Notifications/Reminders Section -->
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

      <!-- Account Selection Dropdown -->
      <div class="account-dropdown-section">
        <label>Select an Account:</label>
        <select class="styled-dropdown" v-model="selectedAccountId" @change="onAccountChange">
          <option v-for="acc in accounts" :key="acc.account_id" :value="acc.account_id">
            {{ acc.name }} ({{ acc.institution_name }})
          </option>
        </select>
      </div>

      <!-- Manual Recurring Transaction (User-Defined) -->
      <div class="manual-recurring-section">
        <label for="manualDescription">Description:</label>
        <input
          id="manualDescription"
          v-model="description"
          type="text"
          placeholder="Ex: Netflix subscription"
          />

        <label for="manualAmount">Amount ($):</label>
        <input
          id="manualAmount"
          v-model.number="amount"
          type="number"
          step="0.01"
        />

        <label for="manualFrequency">Frequency:</label>
        <select id="manualFrequency" v-model="frequency">
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
          <option value="yearly">Yearly</option>
        </select>

        <label for="manualNextDue">Next Due Date:</label>
        <input
          id="manualNextDue"
          v-model="nextDueDate"
          type="date"
        />

        <label for="manualNotes">Notes:</label>
        <input
          id="manualNotes"
          v-model="notes"
          type="text"
          placeholder="Any extra info..."
        />

        <button @click="saveRecurring">Save</button>
      </div>
    </div>
  </template>

  <script>
import axios from "axios";
import api from "@/services/api";

export default {
  name: "RecurringTransactionsSection",
  props: ["provider"],  // Added provider prop to control which API we hit
  data() {
    return {
      accounts: [],
      selectedAccountId: "",
      notifications: [],
      description: "",
      amount: 0.0,
      frequency: "monthly",
      nextDueDate: "",
      notes: "",
      loading: false,
      error: "",
    };
  },
  methods: {
    async fetchAccounts() {
      this.loading = true;
      this.error = "";
      try {
        let response = await axios.get("/api/accounts/get_accounts");
        let accounts = response.data.accounts || response.data;

        this.accounts = accounts.filter(acc => acc.type !== 'liability');

        if (this.accounts.length && !this.selectedAccountId) {
          this.selectedAccountId = this.accounts[0].account_id;
        }
      } catch (err) {
        this.error = err.message || "Error fetching accounts.";
      } finally {
        this.loading = false;
      }
    },

    async fetchRecurringTransactions() {
      if (!this.selectedAccountId) return;
      try {
        const resp = await api.get(`/accounts/${this.selectedAccountId}/recurring`);
        if (resp.status === 'success') {
          this.notifications = resp.reminders;
        } else {
          this.error = "Failed to fetch recurring transactions.";
        }
      } catch (err) {
        this.error = err.message || "Error fetching recurring transactions.";
      }
    },

    async saveRecurring() {
      if (!this.selectedAccountId) return;
      try {
        const payload = {
          amount: this.amount,
          description: this.description || "Unnamed Recurring",
          frequency: this.frequency,
          notes: this.notes,
          next_due_date: this.nextDueDate,
        };
        await api.put(`/accounts/${this.selectedAccountId}/recurringTx`, payload);
        await this.fetchRecurringTransactions();
      } catch (err) {
        this.error = err.message || "Error saving recurring transaction.";
      }
    },

    async onAccountChange() {
      this.notifications = [];
      await this.fetchRecurringTransactions();
    }
  },

  async created() {
    await this.fetchAccounts();
    if (this.selectedAccountId) {
      await this.fetchRecurringTransactions();
    }
  }
};
</script>

<style scoped>
@import '@/styles/global-colors.css';

  .recurring-transactions-section {
    padding: 1rem;
    background-color: var(--gruvbox-bg);
    border-radius: 8px;
    margin-bottom: 1rem;
    color: var(--gruvbox-fg);
    font-family: "Fira Code", monospace;
  }

  .notifications-container {
    background-color: var(--page-bg, #1d2021);
    color: var(--gruvbox-fg);
    padding: 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
  }

  .notification-message {
    margin: 0.25rem 0;
    font-size: 0.9rem;
  }

  /* Account dropdown section */
  .account-dropdown-section {
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }
  .account-dropdown-section .styled-dropdown {
    padding: 0.4rem;
    border-radius: 4px;
    border: 1px solid var(--gruvbox-border);
    background-color: #1d2021;
    color: var(--gruvbox-fg);
    cursor: pointer;
  }

  /* Form for manual recurring */
  .manual-recurring-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .manual-recurring-section input,
  .manual-recurring-section select {
    padding: 0.4rem;
    border-radius: 4px;
    border: 1px solid var(--gruvbox-border);
    background-color: #1d2021;
    color: var(--gruvbox-fg);
  }
  .manual-recurring-section button {
    align-self: flex-start;
    background-color: var(--gruvbox-accent);
    color: var(--gruvbox-fg);
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  .manual-recurring-section button:hover {
    background-color: var(--gruvbox-hover);
  }

</style>

