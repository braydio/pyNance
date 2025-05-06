<template>
  <div class="link-account">
    <h2>Refresh Plaid</h2>
    <div class="button-group">
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
    return {
      isRefreshing: false,
      user_id: import.meta.env.VITE_USER_ID_PLAID,
    };
  },
  methods: {
    async handlePlaidRefresh() {
      this.isRefreshing = true;
      try {
        const response = await axios.post(
          "/api/plaid/transactions/refresh_accounts",
          { user_id: this.user_id }
        );
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
.link-account {
  margin: 0 auto;
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border-top: 8px inset var(--color-bg-secondary);
  border-bottom: 6px outset var(--color-text-muted);
  border-left: 8px inset var(--color-bg-secondary);
  border-right: 6px outset var(--color-text-muted);
  border-radius: 5px;
}

.link-account h2 {
  margin: 5px 1px;
  color: var(--neon-purple);
}

.button-group {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
}

.button-group button {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px groove transparent;
  border-radius: 3px;
  font-weight: bold;
  cursor: pointer;
}

.button-group button:hover {
  color: var(--themed-bg);
  background-color: var(--neon-mint);
}
</style>
