<template>
  <div class="link-account">
    <h2>Refresh Plaid</h2>
    <div class="button-group">
      <input type="date" v-model="startDate" class="date-picker" />
      <input type="date" v-model="endDate" class="date-picker" />
      <button @click="handlePlaidRefresh" :disabled="isRefreshing">
        <span v-if="isRefreshing">Refreshing Plaid Accounts…</span>
        <span v-else>Refresh Plaid Accounts</span>
      </button>
    </div>
  </div>
</template>

<script>
import axios from "axios";
export default {
  name: "RefreshPlaidControls",
  data() {
    const today = new Date().toISOString().slice(0, 10);
    const monthAgo = new Date();
    monthAgo.setDate(monthAgo.getDate() - 30);
    return {
      isRefreshing: false,
      user_id: import.meta.env.VITE_USER_ID_PLAID,
      startDate: monthAgo.toISOString().slice(0, 10),
      endDate: today,
    };
  },
  methods: {
    async handlePlaidRefresh() {
      this.isRefreshing = true;
      try {
        const response = await axios.post("/api/plaid/transactions/refresh_accounts", {
          user_id: this.user_id,
          start_date: this.startDate,
          end_date: this.endDate,
        });
        if (response.data.status === "success") {
          alert("Plaid accounts refreshed: " + response.data.updated_accounts.join(", "));
        } else {
          alert("Error refreshing Plaid accounts: " + response.data.message);
        }
      } catch (err) {
        console.error("Error refreshing Plaid accounts:", err);
        alert("Error refreshing Plaid accounts: " + err.message);
      } finally {
        this.isRefreshing = false;
      }
    },
  },
};
</script>

<style scoped>
.control-block {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px solid var(--color-border-secondary);
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 8px var(--shadow);
  width: 100%;
  max-width: 600px;
}

.control-block h2 {
  margin-bottom: 0.5rem;
  color: var(--neon-purple);
  text-align: center;
}

.button-group {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.button-group button {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px solid var(--color-border-secondary);
  border-radius: 3px;
  font-weight: bold;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.button-group button:hover {
  background-color: var(--neon-mint);
  color: var(--themed-bg);
}

.date-picker {
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  background-color: var(--themed-bg);
  border: 1px solid var(--divider);
  color: var(--color-text-light);
}
</style>

