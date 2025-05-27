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
