<template>
  <div class="dashboard">
    <div>
    <NotificationsBar :messages="notifications" />
    </div>
    <header class="dashboard-header">
      <h1>Hello | Personal Finance | Happy User No. 01 | </h1>
      <h2>
        &gt;Welcome to the financial dashboard – snapshot, viewer quick-look finance profile tracker
      </h2>
      <nav class="menu">
        <!-- Dashboard menu buttons -->
      </nav>
    </header>
    <main class="dashboard-content">
      <section class="charts-section">
        <DailyNetChart />
        <CategoryBreakdownChart />
      </section>
      <section class="snapshot-section">
        <!-- Transactions Section -->
        <div class="transactions-container">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search transactions..."
            class="search-input"
          />  
          <TransactionsTable
            :transactions="filteredTransactions"
            :sort-key="sortKey"
            :sort-order="sortOrder"
            @sort="setSort"
          />
          <div id="pagination-controls">
            <button @click="changePage(-1)" :disabled="currentPage === 1">
              Previous
            </button>
            <span>Page {{ currentPage }} of {{ totalPages }}</span>
            <button @click="changePage(1)" :disabled="currentPage >= totalPages">
              Next
            </button>
          </div>
          <AccountsTable />
        </div>
      </section>
    </main>
    <footer class="dashboard-footer">
      &copy; good dashroad.
    </footer>
  </div>
</template>

<script>
import DailyNetChart from "../components/DailyNetChart.vue";
import CategoryBreakdownChart from "../components/CategoryBreakdownChart.vue";
import AccountsTable from "@/components/AccountsTable.vue";
import TransactionsTable from "@/components/TransactionsTable.vue";
import { useTransactions } from "@/composables/useTransactions.js";

export default {
  name: "Dashboard",
  components: {
    DailyNetChart,
    CategoryBreakdownChart,
    AccountsTable,
    TransactionsTable,
  },
  setup() {
    // Use the composable to get all the transaction-related logic.
    const {
      searchQuery,
      currentPage,
      totalPages,
      filteredTransactions,
      changePage,
      sortKey,
      sortOrder,
      setSort,
    } = useTransactions(15);

    return {
      searchQuery,
      currentPage,
      totalPages,
      filteredTransactions,
      changePage,
      sortKey,
      sortOrder,
      setSort,
    };
  },
};
</script>
