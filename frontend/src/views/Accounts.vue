<template>
  <div class="accounts-page container">
    <header class="accounts-header flex-center p-2">
      <div>
        <h1>Accounts Management</h1>
        <h2>Now with Accounts!</h2>
      </div>
    </header>

    <section class="controls-widget m-2 position-relative">
      <MatchingTransactionUpload />
    </section>

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

    <transition name="slide-horizontal" mode="out-in">
      <div class="accounts-overview card m-2" :key="activeAccountGroup">
        <AccountsTable :accountGroup="activeAccountGroup" />
      </div>
    </transition>

    <div class="account-tabs flex-center m-2">
      <button v-for="group in accountGroups" :key="group" class="btn btn-pill m-1"
        :class="{ 'active-tab': activeAccountGroup === group }" @click="activeAccountGroup = group">
        {{ group }}
      </button>
    </div>

    <footer class="accounts-footer flex-center p-2 mt-3">
      &copy; good dashroad.
    </footer>
  </div>
</template>

<script setup>
import AccountsTable from '@/components/AccountsTable.vue';
import NetYearComparisonChart from '@/components/NetYearComparisonChart.vue';
import AssetsBarTrended from '@/components/AssetsBarTrended.vue';
import AccountsReorderChart from '@/components/AccountsReorderChart.vue';
import MatchingTransactionUpload from '@/components/MatchingTransactionUpload.vue';
import { ref } from 'vue';

const activeAccountGroup = ref("Checking")
const accountGroups = ["Checking", "Savings", "Credit"]
</script>

<style scoped>
.accounts-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--page-bg);
  color: var(--color-text-light);
}

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

.charts-section {
  background-color: var(--theme-bg);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid var(--divider);
  box-shadow: 0 2px 12px var(--shadow);
}

.controls-widget {
  position: relative;
}

.accounts-overview {
  background-color: var(--color-bg-secondary);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid var(--divider);
  box-shadow: 0 2px 12px var(--shadow);
}

.account-tabs button {
  border: 1px solid var(--divider);
}

.account-tabs .active-tab {
  background-color: var(--color-accent-mint) !important;
  color: var(--color-bg-dark) !important;
  box-shadow: 0 0 6px var(--neon-mint);
}

.btn.btn-pill.m-1-hover {
  background-color: var(--color-bg-dark);
}

.accounts-footer {
  background-color: var(--color-bg-secondary);
  border-top: 1px solid var(--themed-border);
  font-size: 0.9rem;
  color: var(--color-text-muted);
  border-radius: 8px;
  box-shadow: 0 -2px 8px var(--shadow);
}
</style>
