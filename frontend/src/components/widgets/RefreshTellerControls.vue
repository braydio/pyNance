<template>
  <div class="link-account">
    <h2>Refresh Teller</h2>
    <div class="button-group">
      <button @click="handleTellerRefresh" :disabled="isRefreshing">
        <span v-if="isRefreshing">Refreshing Teller Accounts…</span>
        <span v-else>Refresh Teller Accounts</span>
      </button>
    </div>
  </div>
</template>

<script>
import axios from "axios";
export default {
  name: "RefreshTellerControls",
  data() {
    return {
      isRefreshing: false,
    };
  },
  methods: {
    async handleTellerRefresh() {
      this.isRefreshing = true;
      try {
        const response = await axios.post("/api/teller/transactions/refresh_accounts");
        if (response.data.status === "success") {
          const updated = response.data.updated_accounts;
          alert("Teller accounts refreshed: " + updated.join(", "));
        } else {
          alert("Error refreshing Teller accounts: " + response.data.message);
        }
      } catch (err) {
        console.error("Error refreshing Teller accounts:", err);
        alert("Error refreshing Teller accounts: " + err.message);
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
</style>

