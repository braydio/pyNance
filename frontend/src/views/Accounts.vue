<template>
  <div class="accounts-page container">
    <!-- Header -->
    <header class="accounts-header flex-center p-2">
      <div>
        <h1>Accounts Management</h1>
        <h2>Now with Accounts!</h2>
      </div>
    </header>

    <!-- Controls Widget -->
    <section class="controls-widget m-2 position-relative">
      <button class="btn btn-pill m-1" @click="toggleControls">Controls</button>
      <transition name="slide-horizontal" mode="out-in">
        <div v-if="showControls" class="card p-2 mt-2 controls-container min-h-[220px]">
          <transition name="slide-horizontal" mode="out-in">
            <div v-if="!showTokenForm" class="flex-center flex-wrap gap-1">
              <LinkAccount class="btn btn-outline btn-pill" @manual-token-click="toggleManualTokenMode" />
              <RefreshPlaidControls class="btn btn-outline btn-pill" />
              <RefreshTellerControls class="btn btn-outline btn-pill" />
            </div>
            <TokenUpload v-else @cancel="toggleManualTokenMode" />
          </transition>
        </div>
      </transition>
    </section>

    <!-- Charts Section -->
    <section class="charts-section grid-3col gap-2 m-2">
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

    <!-- Accounts Table -->
    <transition name="slide-horizontal" mode="out-in">
      <div class="accounts-overview card m-2" :key="activeAccountGroup">
        <AccountsTable :accountGroup="activeAccountGroup" />
      </div>
    </transition>

    <!-- Account Group Tabs -->
    <div class="account-tabs flex-center m-2">
      <button v-for="group in accountGroups" :key="group" class="btn btn-pill m-1"
        :class="{ 'active-tab': activeAccountGroup === group }" @click="activeAccountGroup = group">
        {{ group }}
      </button>
    </div>

    <!-- Footer -->
    <footer class="accounts-footer flex-center p-2 mt-3">
      &copy; good dashroad.
    </footer>
  </div>
</template>

<script setup>
import LinkAccount from "@/components/LinkAccount.vue";
import AccountsTable from "@/components/AccountsTable.vue";
import NetYearComparisonChart from "@/components/NetYearComparisonChart.vue";
import AssetsBarTrended from "@/components/AssetsBarTrended.vue";
import RefreshTellerControls from "@/components/RefreshTellerControls.vue";
import RefreshPlaidControls from "@/components/RefreshPlaidControls.vue";
import AccountsReorderChart from "@/components/AccountsReorderChart.vue";
import TokenUpload from "@/components/TokenUpload.vue";
import { ref } from 'vue';

const userName = import.meta.env.VITE_USER_ID_PLAID;
const currentDate = new Date().toLocaleDateString(undefined, {
  month: "long",
  day: "numeric",
  year: "numeric",
})

const activeAccountGroup = ref("Checking")
const accountGroups = ["Checking", "Savings", "Credit"]
const showControls = ref(true)
const showTokenForm = ref(false)

function toggleControls() {
  showControls.value = !showControls.value
}

function toggleManualTokenMode() {
  showTokenForm.value = !showTokenForm.value
}
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

/* Layout Styling */
.accounts-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--page-bg);
  color: var(--color-text-light);
}

/* Header */
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

.btn btn-pill m-1-hover {
  background-color: var(--color-bg-dark);
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
