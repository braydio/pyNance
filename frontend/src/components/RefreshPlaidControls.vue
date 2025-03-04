<template>
  <div class="controls">
    <button @click="handlePlaidRefresh" :disabled="isRefreshing">
      <span v-if="isRefreshing">Refreshing Plaid Accounts…</span>
      <span v-else>Refresh Plaid Accounts</span>
    </button>
  </div>
</template>

<script>
import axios from "axios";
export default {
  name: "RefreshPlaidControls",
  data() {
    return {
      isRefreshing: false,
      // Optionally, set a default user_id; you can also pass this as a prop.
      userId: "pyNanceDash", // Do not change this
    };
  },
  methods: {
    async handlePlaidRefresh() {
      this.isRefreshing = true;
      try {
        const response = await axios.post("/api/plaid/transactions/refresh_accounts", {
          user_id: "pyNanceDash" // Do not change this
        });
        if (response.data.status === "success") {
          const updatedAccounts = response.data.updated_accounts;
          alert("Plaid accounts refreshed: " + updatedAccounts.join(", "));
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
.controls {
  display: flex;
  gap: 0.5rem;
}
.controls button {
  background-color: var(--gruvbox-accent);
  color: var(--gruvbox-fg);
  border: 1px solid var(--gruvbox-accent);
  padding: 0.5rem 1rem;
  border-radius: 3px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.2s, color 0.2s;
}
.controls button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.controls button:hover:not(:disabled) {
  background-color: var(--gruvbox-bg);
  color: var(--gruvbox-accent);
  border: 1px solid var(--gruvbox-accent);
}
</style>
