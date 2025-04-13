<template>
  <div class="controls">
    <button @click="handleTellerRefresh" :disabled="isRefreshing">
      <span v-if="isRefreshing">Refreshing Teller Accounts…</span>
      <span v-else>Refresh Teller Accounts</span>
    </button>
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

.controls {
  display: flex;
  gap: 0.5rem;
}
.controls button {
  background-color: var(--color-bg-dark);
  color: var(--color-text-light);
  border: 1px solid transparent;
  padding: 0.5rem 1rem;
  border-radius: 3px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.2s, color 0.2s;
}
.controls button:disabled {
  opacity: 0.8;
  cursor: not-allowed;
}
.controls button:hover:not(:disabled) {
  background-color: var(--button-hover);
  color: var(--gruvbox-accent);
  border: 1px solid transparent;
}

</style>
