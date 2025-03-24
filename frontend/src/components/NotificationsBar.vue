<template>
  <div>
    <div class="notifications-container">
      <p 
        v-for="(notif, idx) in notifications" 
        :key="idx" 
        class="notification-message"
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

export default {
  props: ["accountId", "currentApr"],
  data() {
    return {
      notifications: [],
      txRecur: this.currentApr || 0
    };
  },
  methods: {
    async saveRecurring() {
      try {
        const resp = await axios.put(`/api/accounts/${this.accountId}/recurringTx`, {
          amount: this.txRecur
        });
        console.log("Recurring transaction updated:", resp.data);
        await this.fetchRecurringTransactions();
      } catch (err) {
        console.error("Error updating recurring transaction:", err);
      }
    },
    async fetchRecurringTransactions() {
  try {
    const resp = await axios.get(`/api/accounts/${this.accountId}/recurring`);
    if (resp.data.status === "success") {
      this.notifications = resp.data.reminders;
    }
  } catch (err) {
    console.error("Error fetching recurring transactions:", err);
  }
}
  },
  created() {
    this.fetchRecurringTransactions();
  },
};
</script>


<style scoped>
.notifications-container {
  background-color: #333;
  color: #fff;
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 6px;
}

.notification-message {
  margin: 0.25rem 0;
}
</style>
