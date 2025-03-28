<template>
  <div class="accounts-page">
    <header class="accounts-header">
      <h1>Accounts Management</h1>
    </header>

    <!-- Charts -->
    <section class="charts-section">
      <NetYearComparisonChart />
      <AssetsBarTrended />
    </section>

    <!-- Controls Grouping -->
    <section class="account-controls">
      <LinkAccount />
      <RefreshControls :onFetch="fetchAccounts" :onRefresh="refreshActivity" />
      <RefreshPlaidControls />
      <RefreshTellerControls />
    </section>

    <!-- Accounts Table -->
    <div class="accounts-overview">
      <AccountsTable />
    </div>

    <!-- Footer -->
    <footer class="accounts-footer">
      &copy; good dashroad.
    </footer>
  </div>
</template>

<script>
import LinkAccount from '@/components/LinkAccount.vue';
import AccountsTable from '@/components/AccountsTable.vue';
import AccountsReorderChart from '@/components/AccountsReorderChart.vue';
import NetYearComparisonChart from '@/components/NetYearComparisonChart.vue';
import AssetsBarTrended from '@/components/AssetsBarTrended.vue';
import RefreshTellerControls from '@/components/RefreshTellerControls.vue';
import RefreshPlaidControls from '@/components/RefreshPlaidControls.vue';

export default {
  name: "Accounts",
  components: {
    LinkAccount,
    AccountsTable,
    AccountsReorderChart,
    NetYearComparisonChart,
    AssetsBarTrended,
    RefreshTellerControls,
    RefreshPlaidControls,
  }
};
</script>

<style scoped>
@import '@/styles/global-colors.css';

.accounts-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--page-bg);
  color: var(--color-text-light);
}
.account-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 1rem;
  background-color: var(--background);
  border-radius: 8px;
  margin-bottom: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
}
.accounts-header {
  background-color: var(--color-bg-secondary);
  padding: 1rem;
  text-align: center;
  border-bottom: 1px solid var(--themed-border);
}
.accounts-header h1 {
  margin: 0;
  color: var(--color-accent-yellow);
  font-size: 2rem;
}
.accounts-overview {
  margin-bottom: 1rem;
}
.accounts-section {
  background-color: var(--color-bg-secondary);
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}
.refresh-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1rem;
}
.accounts-drag {
  margin-bottom: 1rem;
}
.accounts-footer {
  background-color: var(--color-bg-secondary);
  padding: 1rem;
  text-align: center;
  border-top: 1px solid var(--themed-border);
  font-size: 0.9rem;
  color: var(--color-text-light);
}
</style>
