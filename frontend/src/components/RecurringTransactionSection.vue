<template>
  <div class="recurring-transactions-section">
    <!-- Notifications/Reminders Section -->
    <div class="notifications-container" v-if="notifications.length">
      <h3>Upcoming Recurring Transactions</h3>
      <p v-for="(notif, idx) in notifications" :key="idx" class="notification-message">
        {{ notif }}
      </p>
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

      <label for="manualTxId">Transaction ID:</label>
      <input
        id="manualTxId"
        v-model="transactionId"
        type="text"
        placeholder="tx_abc123"
      />

      <button @click="saveRecurring" :disabled="loading">
        {{ loading ? 'Saving...' : 'Save' }}
      </button>
    </div>
  </div>
</template>

<script>
import { createRecurringTransaction } from "@/api/recurring";

export default {
  name: "RecurringTransactionsSection",
  data() {
    return {
      transactionId: "",
      description: "",
      amount: 0.0,
      frequency: "monthly",
      nextDueDate: "",
      notes: "",
      loading: false,
      error: "",
      notifications: []
    };
  },
  methods: {
    async saveRecurring() {
      if (!this.transactionId) return;
      this.loading = true;
      try {
        const payload = {
          frequency: this.frequency,
          next_due_date: this.nextDueDate,
          notes: this.notes || this.description || "Untitled Recurring",
        };
        await createRecurringTransaction(this.transactionId, payload);
        this.notifications.push(`Recurring rule saved for transaction ${this.transactionId}`);
      } catch (err) {
        this.error = err.message || "Error saving recurring transaction.";
      } finally {
        this.loading = false;
      }
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

