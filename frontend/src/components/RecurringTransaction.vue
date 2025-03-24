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

    <!-- Manual Recurring Transaction (Optional) -->
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
import api from '@/services/api';

export default {
  props: ["accountId"],
  data() {
    return {
      notifications: [],
      txAmount: 0
    };
  },
  methods: {
    async fetchRecurringTransactions() {
      try {
        // example usage: GET /api/accounts/:account_id/recurring
        const resp = await api.get(`/accounts/${this.accountId}/recurring`);
        if (resp.status === 'success') {
          this.notifications = resp.reminders;
        } else {
          console.warn('Failed to fetch recurring transactions:', resp);
        }
      } catch (err) {
        console.error('Error fetching recurring transactions:', err);
      }
    },

    async saveRecurring() {
      try {
        // example usage: PUT /api/accounts/:account_id/recurringTx
        const resp = await api.put(`/accounts/${this.accountId}/recurringTx`, {
          amount: this.txAmount
        });
        console.log('Recurring transaction saved:', resp);
        await this.fetchRecurringTransactions();
      } catch (err) {
        console.error('Error saving recurring transaction:', err);
      }
    }
  },
  created() {
    this.fetchRecurringTransactions();
  }
};
</script>

<style scoped>
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

.manual-recurring-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.manual-recurring-section input {
  padding: 0.5rem;
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
