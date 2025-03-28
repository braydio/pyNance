<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <h1>Hello {{ userName }}!</h1>
      <h2>Today is {{ currentDate }}</h2>
      <h2>and things are looking quite bleak.</h2>
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
import NotificationsBar from "@/components/NotificationsBar.vue";
import RecurringTransactionSection from "@/components/RecurringTransactionSection.vue";
import RecurringTransaction from "@/components/RecurringTransaction.vue";

export default {
  name: "Dashboard",
  components: {
    DailyNetChart,
    CategoryBreakdownChart,
    AccountsTable,
    TransactionsTable,
    NotificationsBar,
    RecurringTransactionSection,
    RecurringTransaction,
  },
  setup() {
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
  data() {
    return {
      userName: import.meta.env.VITE_USER_ID_PLAID,
      currentDate: new Date().toLocaleDateString(undefined, {
        month: "long",
        day: "numeric",
        year: "numeric",
      }),
    };
  },
};
</script>

<style scoped>
/* Import the global color variables */
@import "@/styles/global-colors.css";

.dashboard {
  background-color: var(--page-bg);
  color: var(--themed-fg);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.dashboard-header {
  background-color: var(--color-bg-dark);
  padding: 1rem;
  border-bottom: 1px solid var(--themed-border);
  text-align: center;
  margin-bottom: 1rem;
}
.dashboard-header h1,
.dashboard-header h2 {
  margin: 0.5rem 0;
  color: var(--color-text-light);
}

/* Main Content */
.dashboard-content {
  flex: 1;
  background-color: var(--background);
  padding: 1rem;
}

/* Charts Section */
.charts-section {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 2rem;
  background-color: var(--color-bg-secondary);
  padding: 1rem;
  border-radius: 8px;
}

/* Transactions Section */
.transactions-container {
  background-color: var(--color-bg-secondary);
  padding: 1rem;
  border-radius: 8px;
}
.search-input {
  margin-bottom: 1rem;
  padding: 0.5rem;
  color: var(--themed-fg);
  background-color: var(--page-bg);
  border: 1px solid var(--themed-border);
}

/* Footer */
.dashboard-footer {
  background-color: var(--color-bg-dark);
  color: var(--color-text-light);
  padding: 1rem;
  text-align: center;
  border-top: 1px solid var(--themed-border);
}
</style>
