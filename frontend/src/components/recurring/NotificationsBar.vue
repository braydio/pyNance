<template>
  <div>
    <div class="bg-[#333] text-white p-4 mb-4 rounded-[6px]">
      <p 
        v-for="(notif, idx) in notifications" 
        :key="idx" 
        class="my-1"
      >
        {{ notif }}
      </p>
    </div>

    <div class="recurring-tx-section">
      <label>Recurring Transaction Amount ($):</label>
      <input v-model="txRecur" type="number" step="0.01" />
      <button @click="saveRecurring">Save Recurring Transaction</button>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { sanitizeForLog } from "../../utils/sanitize.js";

// Component to display account notifications and manage recurring transactions.
export default {
  props: ["accountId", "currentApr"],
  data() {
    return {
      notifications: [],
      txRecur: this.currentApr || 0
    };
  },
  methods: {
    /**
     * Save the recurring transaction amount and refresh the reminder list.
     */
    async saveRecurring() {
      try {
        const resp = await axios.put(`/api/accounts/${this.accountId}/recurringTx`, {
          amount: this.txRecur
        });
        console.log("Recurring transaction updated:", sanitizeForLog(resp.data));
        await this.fetchRecurringTransactions();
      } catch (err) {
        console.error(
          "Error updating recurring transaction:",
          sanitizeForLog(err.message || err)
        );
      }
    },
    /**
     * Load existing recurring transaction reminders for the account.
     */
    async fetchRecurringTransactions() {
      try {
        const resp = await axios.get(`/api/accounts/${this.accountId}/recurring`);
        if (resp.data.status === "success") {
          this.notifications = resp.data.reminders;
        }
      } catch (err) {
        console.error(
          "Error fetching recurring transactions:",
          sanitizeForLog(err.message || err)
        );
      }
    }
  },
  created() {
    this.fetchRecurringTransactions();
  },
};
</script>
