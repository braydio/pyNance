<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <div class="greeting-block">
        <h1>Ah, {{ userName }} my old friend!</h1>
        <h2 class="date">Today is {{ currentDate }}</h2>
        <h2 class="vibe">and things are looking quite bleak.</h2>
      </div>
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
  padding: 1.5rem 1rem;
  border-bottom: 1px solid var(--themed-border);
  text-align: center;
  margin-bottom: 1rem;
  box-shadow: 0 4px 10px var(--shadow);
}
.greeting-block h1 {
  margin: 0;
  font-size: 2rem;
  color: var(--color-accent-mint);
  text-shadow: 0 0 6px var(--neon-mint);
}
.greeting-block h2 {
  margin: 0.3rem 0;
  color: var(--color-text-muted);
  font-size: 1.1rem;
}
.greeting-block .vibe {
  font-style: italic;
  color: var(--color-accent-magenta);
}

.menu {
  margin-top: 1rem;
}

/* Main Content */
.dashboard-content {
  flex: 1;
  background-color: var(--background);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Charts Section */
.charts-section {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  background-color: var(--color-bg-secondary);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid var(--divider);
  box-shadow: 0 2px 12px var(--shadow);
}

/* Transactions Section */
.transactions-container {
  background-color: var(--color-bg-secondary);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid var(--divider);
  box-shadow: 0 2px 12px var(--shadow);
}
.search-input {
  margin-bottom: 1rem;
  padding: 0.5rem;
  color: var(--themed-fg);
  background-color: var(--page-bg);
  border: 1px solid var(--themed-border);
  border-radius: 4px;
  width: 100%;
  font-family: "Fira Code", monospace;
}

#pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 1rem 0;
  font-size: 0.95rem;
  color: var(--color-text-muted);
}
#pagination-controls button {
  padding: 0.4rem 0.75rem;
  background-color: var(--button-bg);
  color: var(--color-text-light);
  border: 1px solid var(--themed-border);
  border-radius: 4px;
  cursor: pointer;
  font-family: "Fira Code", monospace;
  transition: background-color 0.2s;
}
#pagination-controls button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
#pagination-controls button:hover:enabled {
  background-color: var(--button-hover-bg);
}

/* Footer */
.dashboard-footer {
  background-color: var(--color-bg-dark);
  color: var(--color-text-light);
  padding: 1rem;
  text-align: center;
  border-top: 1px solid var(--themed-border);
  font-size: 0.9rem;
}
</style>
