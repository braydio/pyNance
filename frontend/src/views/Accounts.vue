<template>
  <div class="accounts-page">
    <div class="accounts-overview">
      <h1>Accounts Overview</h1>
      <!-- Render the AccountsTable component -->
      <AccountsTable />
    </div>
    <div class="accounts-drag">
      <!-- Render the draggable accounts chart -->
      <AccountsReorderChart />
    </div>
  </div>
</template>

<script>
import AccountsTable from '../components/AccountsTable.vue';
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
