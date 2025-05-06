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
