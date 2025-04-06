<template>
  <!-- Container to center page and set max-width -->
  <div class="accounts-page container">

    <!-- Header -->
    <header class="accounts-header flex-center p-2">
      <div>
        <h1>Accounts Management</h1>
        <h2>Now with Accounts!</h2>
      </div>
    </header>

    <!-- Charts Section -->
    <section class="charts-section grid-3col gap-2 m-2">
      <!-- Wrap each chart in a card for consistent styling -->
      <div class="card">
        <NetYearComparisonChart />
      </div>
      <div class="card">
        <AssetsBarTrended />
      </div>
      <div class="card">
        <AccountsReorderChart />
      </div>
    </section>

    
    <!-- Controls Widget: Hideable section attached to the Accounts Table -->
    <section class="controls-widget m-2 position-relative">
      <!-- Toggle icon positioned statically -->
      <button class="btn btn-pill m-1" @click="toggleControls">Controls
      </button>
      <transition name="slide-horizontal" mode="out-in">
        <div v-if="showControls" class="card p-2 mt-2 controls-container">
          <div class="flex-center gap-1">
            <LinkAccount class="btn btn-outline btn-pill" />
            <RefreshPlaidControls class="btn btn-outline btn-pill" />
            <RefreshTellerControls class="btn btn-outline btn-pill" />
          </div>
        </div>
      </transition>
    </section>
    <!-- Accounts Table with Slide Transition -->
    <transition name="slide-horizontal" mode="out-in">
      <div class="accounts-overview card m-2" :key="activeAccountGroup">
        <AccountsTable :accountGroup="activeAccountGroup" />
      </div>
    </transition>

    <!-- Account Group Tabs -->
    <div class="account-tabs flex-center m-2">
      <button
        v-for="group in accountGroups"
        :key="group"
        class="btn btn-pill m-1"
        :class="{ 'active-tab': activeAccountGroup === group }"
        @click="activeAccountGroup = group"
      >
        {{ group }}
      </button>
    </div>

    <!-- Footer -->
    <footer class="accounts-footer flex-center p-2 mt-3">
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
      showControls: true, // Controls widget is shown by default
    };
  },
  methods: {
    toggleControls() {
      this.showControls = !this.showControls;
    },
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
/* Slide-horizontal Transition */
.slide-horizontal-enter-active,
.slide-horizontal-leave-active {
  transition: transform 0.4s ease, opacity 0.4s ease;
}
.slide-horizontal-enter-from {
  transform: translateX(-100%);
  opacity: 0;
}
.slide-horizontal-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

/* Page Layout */
.accounts-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--page-bg);
  color: var(--color-text-light);
}

/* Header styling */
.accounts-header {
  background-color: var(--color-bg-secondary);
  border-bottom: 1px solid var(--themed-border);
  border-radius: 8px;
  box-shadow: 0 4px 12px var(--shadow);
  text-align: center;
}
.accounts-header h1 {
  margin: 0;
  color: var(--color-accent-yellow);
  font-size: 2rem;
  text-shadow: 0 0 6px var(--color-accent-yellow);
}

/* Charts Section */
.charts-section {
  background-color: var(--themed-bg);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid var(--divider);
  box-shadow: 0 2px 12px var(--shadow);
}

/* Controls Widget */
.controls-widget {
  /* Ensure relative positioning for the static toggle icon */
  position: relative;
}



/* Accounts Table Section */
.accounts-overview {
  background-color: var(--color-bg-secondary);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid var(--divider);
  box-shadow: 0 2px 12px var(--shadow);
}

/* Account Tabs */
.account-tabs button {
  border: 1px solid var(--divider);
}
.account-tabs .active-tab {
  background-color: var(--color-accent-mint) !important;
  color: var(--color-bg-dark) !important;
  box-shadow: 0 0 6px var(--neon-mint);
}
.btn btn-pill m-1-hover{
  background-color: var(--color-bg-dark)
}
/* Footer */
.accounts-footer {
  background-color: var(--color-bg-secondary);
  border-top: 1px solid var(--themed-border);
  font-size: 0.9rem;
  color: var(--color-text-muted);
  border-radius: 8px;
  box-shadow: 0 -2px 8px var(--shadow);
}
</style>