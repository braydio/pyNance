<template>
  <div class="accounts-page">
    <div class="accounts-overview">
      <h1>Accounts Management</h1>
      <!-- Render the AccountsTable component -->
      <div class="accounts-section">
        <!-- Teller Connect Button -->
        <button id="new-link-plaid">Plaid Link</button>
        <button id="new-link-teller">Teller.io</button>
      
      <AccountsTable />
    </div>
    </div>
    <div class="accounts-drag">
      <!-- Render the draggable accounts chart -->
      <AccountsReorderChart />
    </div>
  </div>
</template>

<script>
import AccountsTable from '@/components/AccountsTable.vue';
import AccountsReorderChart from '@/components/AccountsReorderChart.vue';

export default {
  name: "Accounts",
  components: {
    AccountsTable,
    AccountsReorderChart
  }
};
</script>

<style scoped>
/* =============================================================================
   Accounts Table Container
   ============================================================================= */
/* Removed border since the section container now provides separation */
.accounts-table {
  background-color: var(--gruvbox-bg);
  color: var(--gruvbox-fg);
  padding: 1rem;
  border-radius: 4px;
}

/* Title Styling for Accounts Table */
.accounts-table h2 {
  margin-top: 0;
  color: var(--gruvbox-yl);
}

.accounts-page {
  padding: 1rem;
}
.accounts-overview {
  margin-bottom: 1rem;
}
.accounts-drag {
  margin-bottom: 1rem;
}
</style>
