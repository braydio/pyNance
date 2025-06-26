<template>
  <div class="link-account">
    <h2>Refresh Teller</h2>
    <div class="button-group">
      <input type="date" v-model="startDate" class="date-picker" />
      <input type="date" v-model="endDate" class="date-picker" />
      <div class="account-select">
        <button type="button" @click="toggleDropdown">Select Accounts</button>
        <div v-if="dropdownOpen" class="dropdown-menu">
          <label v-for="acct in accounts" :key="acct.account_id">
            <input
              type="checkbox"
              :value="acct.account_id"
              v-model="selectedAccounts"
            />
            {{ acct.name }}
          </label>
        </div>
      </div>
      <button @click="handleTellerRefresh" :disabled="isRefreshing">
        <span v-if="isRefreshing">Refreshing Teller Accounts…</span>
        <span v-else>Refresh Teller Accounts</span>
      </button>
    </div>
  </div>
</template>

<script>
import api from "@/services/api";
export default {
  name: "RefreshTellerControls",
  data() {
    const today = new Date().toISOString().slice(0, 10);
    const monthAgo = new Date();
    monthAgo.setDate(monthAgo.getDate() - 30);
    return {
      isRefreshing: false,
      startDate: monthAgo.toISOString().slice(0, 10),
      endDate: today,
      accounts: [],
      selectedAccounts: [],
      dropdownOpen: false,
    };
  },
  methods: {
    toggleDropdown() {
      this.dropdownOpen = !this.dropdownOpen;
    },
    async loadAccounts() {
      try {
        const resp = await api.getAccounts();
        if (resp?.status === "success" && resp.accounts) {
          this.accounts = resp.accounts;
        }
      } catch (err) {
        console.error("Failed to load accounts", err);
        alert("Failed to load accounts: " + err.message);
      }
    },
    async handleTellerRefresh() {
      this.isRefreshing = true;
      try {
        const response = await api.refreshAccounts({
          start_date: this.startDate,
          end_date: this.endDate,
          account_ids: this.selectedAccounts,
        });
        if (response.status === "success") {
          const counts = response.refreshed_counts || {};
          const parts = Object.entries(counts).map(
            ([inst, count]) => `${count} account${count > 1 ? "s" : ""} at ${inst}`
          );
          alert("Refreshed " + parts.join(", "));
        } else {
          alert("Error refreshing Teller accounts: " + response.message);
        }
      } catch (err) {
        console.error("Error refreshing Teller accounts:", err);
        alert("Error refreshing Teller accounts: " + err.message);
      } finally {
        this.isRefreshing = false;
      }
    },
  },
  mounted() {
    this.loadAccounts();
  },
};
</script>

<style scoped>
@reference "../../assets/css/main.css";
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

.date-picker {
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  background-color: var(--themed-bg);
  border: 1px solid var(--divider);
  color: var(--color-text-light);
}

.account-select {
  position: relative;
}

.account-select button {
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  background-color: var(--themed-bg);
  border: 1px solid var(--divider);
  color: var(--color-text-light);
}

.dropdown-menu {
  position: absolute;
  background-color: var(--themed-bg);
  border: 1px solid var(--divider);
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
}
</style>

