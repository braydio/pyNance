<template>
  <div class="accounts-page">
    <header class="accounts-header">
      <h1>Accounts Management</h1>
      <h2>Now with Transitions!</h2>
    </header>

    <!-- Controls Grouping -->
    <section class="account-controls">
      <LinkAccount />
      <RefreshPlaidControls />
      <RefreshTellerControls />
    </section>

    <!-- Charts Section with Animated Transition -->
    <section class="charts-section">
      <transition-group name="fade" tag="div" class="charts-wrapper">
        <NetYearComparisonChart key="net-year" />
        <AssetsBarTrended key="assets-bar" />
        <AccountsReorderChart key="top-accounts" />
      </transition-group>
    </section>

    <!-- Account Group Tabs -->
    <div class="account-tabs">
      <button
        v-for="group in accountGroups"
        :key="group"
        :class="{ 'active-tab': activeAccountGroup === group }"
        @click="activeAccountGroup = group"
      >
        {{ group }}
      </button>
    </div>

    <!-- Accounts Table with Animated Transition -->
    <transition name="fade" mode="out-in">
      <div class="accounts-overview" :key="activeAccountGroup">
        <AccountsTable :accountGroup="activeAccountGroup" />
      </div>
    </transition>

    <!-- Footer -->
    <footer class="accounts-footer">
      &copy; good dashroad.
    </footer>
  </div>
</template>

<script>
import LinkAccount from "@/components/LinkAccount.vue";
import AccountsTable from "@/components/AccountsTable.vue";
import NetYearComparisonChart from "@/components/NetYearComparisonChart.vue";
import AssetsBarTrended from "@/components/AssetsBarTrended.vue";
import RefreshTellerControls from "@/components/RefreshTellerControls.vue";
import RefreshPlaidControls from "@/components/RefreshPlaidControls.vue";
import RefreshControls from "@/components/RefreshControls.vue"; // Assuming this exists
import AccountsReorderChart from "@/components/AccountsReorderChart.vue";

export default {
  name: "Accounts",
  components: {
    LinkAccount,
    AccountsTable,
    NetYearComparisonChart,
    AssetsBarTrended,
    RefreshTellerControls,
    RefreshPlaidControls,
    RefreshControls,
    AccountsReorderChart,
  },
  data() {
    return {
      userName: import.meta.env.VITE_USER_ID_PLAID,
      currentDate: new Date().toLocaleDateString(undefined, {
        month: "long",
        day: "numeric",
        year: "numeric",
      }),
      activeAccountGroup: "Checking",
      accountGroups: ["Checking", "Savings", "Credit"],
    };
  },
  methods: {
    // Dummy refresh methods – replace with your logic.
    fetchAccounts() {
      console.log("Fetching accounts...");
    },
    refreshActivity() {
      console.log("Refreshing activity...");
    },
  },
};
</script>

<style scoped>

/* Fade Transition Classes */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.accounts-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--page-bg);
  color: var(--color-text-light);
  padding: 1rem;
  gap: 2rem;
}

/* Updated Header to Match Dashboard */
.accounts-header {
  background-color: var(--color-bg-secondary);
  padding: 1.5rem 1rem;
  text-align: center;
  border-bottom: 1px solid var(--themed-border);
  border-radius: 12px;
  box-shadow: 0 4px 12px var(--shadow);
}
.accounts-header h1 {
  margin: 0;
  color: var(--color-accent-yellow);
  font-size: 2rem;
  text-shadow: 0 0 6px var(--);
}

/* Charts Section */
.charts-section {
  background-color: var(--themed-bg);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid var(--divider);
  box-shadow: 0 2px 12px var(--shadow);
}
.charts-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

/* Controls Section */
.account-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  padding: 1rem;
  background-color: var(--background);
  border-radius: 12px;
  border: 1px solid var(--divider);
  box-shadow: 0 2px 8px var(--shadow);
}

/* Account Tabs */
.account-tabs {
  display: flex;
  justify-content: center;
  gap: 1rem;
}
.account-tabs button {
  padding: 0.5rem 1rem;
  background-color: var(--button-bg);
  color: var(--color-text-light);
  border: 1px solid var(--themed-border);
  border-radius: 6px;
  cursor: pointer;
  font-family: "Fira Code", monospace;
  transition: background-color 0.3s;
}
.account-tabs button:hover {
  background-color: var(--button-hover-bg);
}
.account-tabs .active-tab {
  background-color: var(--color-accent-mint);
  color: var(--color-bg-dark);
  font-weight: bold;
  box-shadow: 0 0 6px var(--neon-mint);
}

/* Accounts Table Section */
.accounts-overview {
  background-color: var(--color-bg-secondary);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid var(--divider);
  box-shadow: 0 2px 12px var(--shadow);
}

/* Footer */
.accounts-footer {
  background-color: var(--color-bg-secondary);
  padding: 1rem;
  text-align: center;
  border-top: 1px solid var(--themed-border);
  font-size: 0.9rem;
  color: var(--color-text-muted);
  border-radius: 12px;
  box-shadow: 0 -2px 8px var(--shadow);
}
</style>

