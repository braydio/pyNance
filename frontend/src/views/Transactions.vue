<template>
  <div class="transactions-page">
    <!-- Header -->
    <header class="transactions-header">
      <div>
        <h1 class="heading-lg">Transactions</h1>
        <h3 class="text-muted mb-2">View and manage your transactions</h3>
      </div>
    </header>

    <main>
      <!-- File Importer -->
      <ImportFileSelector class="mb-4" />

      <!-- Search + Controls -->
      <div class="controls mb-2">
        <input v-model="searchQuery" type="text" placeholder="Search transactions..." class="search-input" />
      </div>

      <!-- Main Table -->
      <UpdateTransactionsTable :transactions="filteredTransactions" :sort-key="sortKey" :sort-order="sortOrder"
        @sort="setSort" />

      <!-- Pagination -->
      <div id="pagination-controls" class="mt-3 flex-center gap-2">
        <button class="btn" @click="changePage(-1)" :disabled="currentPage === 1">
          Prev
        </button>
        <span class="text-muted">Page {{ currentPage }} of {{ totalPages }}</span>
        <button class="btn" @click="changePage(1)" :disabled="currentPage >= totalPages">
          Next
        </button>
      </div>

      <!-- Recurring Transactions (Optional) -->
      <div class="mt-6">
        <RecurringTransactionSection provider="plaid" />
      </div>
    </main>
  </div>
</template>

<script>
import { useTransactions } from "@/composables/useTransactions.js"
import UpdateTransactionsTable from "@/components/UpdateTransactionsTable.vue"
import RecurringTransactionSection from "@/components/RecurringTransactionSection.vue"
import ImportFileSelector from "@/components/ImportFileSelector.vue"

export default {
  name: "Transactions",
  components: {
    UpdateTransactionsTable,
    RecurringTransactionSection,
    ImportFileSelector,
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
    } = useTransactions(15)

    return {
      searchQuery,
      currentPage,
      totalPages,
      filteredTransactions,
      changePage,
      sortKey,
      sortOrder,
      setSort,
    }
  },
}
</script>

<style scoped>
.transactions-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--page-bg);
  color: var(--color-text-light);
  padding: 1rem;
  gap: 2rem;
}

.transactions-header {
  background-color: var(--color-bg-secondary);
  padding: 1.5rem;
  text-align: center;
  border-radius: 12px;
  box-shadow: 0 4px 14px var(--shadow);
}

.transactions-header h1 {
  color: var(--color-accent-yellow);
  margin: 0;
  font-size: 2.2rem;
  text-shadow: 0 0 6px var(--color-accent-yellow);
}

.controls {
  margin-bottom: 1rem;
}

.search-input {
  width: 100%;
  max-width: 320px;
  padding: 0.5rem 1rem;
  border: 1px solid var(--divider);
  border-radius: 6px;
  background-color: var(--color-bg-secondary);
  color: var(--color-text-light);
  font-family: var(--font-mono);
}

#pagination-controls {
  margin-top: 1rem;
  text-align: center;
}

button.btn {
  background-color: var(--button-bg);
  color: var(--color-text-light);
  border: 1px solid var(--divider);
  border-radius: 6px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
}

button.btn:hover:not(:disabled) {
  background-color: var(--button-hover-bg);
  transform: translateY(-1px);
  box-shadow: 0 0 6px var(--hover-glow);
}

button.btn:disabled {
  background-color: #444;
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
