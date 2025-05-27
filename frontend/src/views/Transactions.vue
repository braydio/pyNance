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
      <!-- Top Controls -->
      <div class="top-controls">
        <ImportFileSelector class="import-section" />
        <input v-model="searchQuery" type="text" placeholder="Search transactions..." class="search-input" />
      </div>

      <!-- Main Table -->
      <UpdateTransactionsTable :transactions="filteredTransactions" :sort-key="sortKey" :sort-order="sortOrder"
        @sort="setSort" @editRecurringFromTransaction="prefillRecurringFromTransaction" />

      <!-- Pagination -->
      <div id="pagination-controls">
        <button class="btn" @click="changePage(-1)" :disabled="currentPage === 1">
          Prev
        </button>
        <span class="text-muted">Page {{ currentPage }} of {{ totalPages }}</span>
        <button class="btn" @click="changePage(1)" :disabled="currentPage >= totalPages">
          Next
        </button>
      </div>

      <!-- Recurring Transactions -->
      <RecurringTransactionSection ref="recurringFormRef" provider="plaid" class="mt-8" />
    </main>
  </div>
</template>

<script>
import { ref } from "vue"
import { useTransactions } from "@/composables/useTransactions.js"
import UpdateTransactionsTable from "@/components/tables//UpdateTransactionsTable.vue"
import RecurringTransactionSection from "@/components/recurring/RecurringTransactionSection.vue"
import ImportFileSelector from "@/components/forms//ImportFileSelector.vue"

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

    const recurringFormRef = ref(null)

    function prefillRecurringFromTransaction(tx) {
      if (recurringFormRef.value) {
        recurringFormRef.value.transactionId = tx.transaction_id || ''
        recurringFormRef.value.description = tx.description || ''
        recurringFormRef.value.amount = parseFloat(tx.amount) || 0
        recurringFormRef.value.notes = tx.notes || ''
        recurringFormRef.value.showForm = true
      }
    }

    return {
      searchQuery,
      currentPage,
      totalPages,
      filteredTransactions,
      changePage,
      sortKey,
      sortOrder,
      setSort,
      recurringFormRef,
      prefillRecurringFromTransaction
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
  padding: 1.5rem;
  gap: 2rem;
}

.import-section {
  margin-bottom: 1.5rem;
}

.transactions-header {
  background-color: var(--color-bg-secondary);
  padding: 1.5rem 2rem;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 4px 14px var(--shadow);
}

.transactions-header h1 {
  color: var(--color-accent-yellow);
  font-size: 2.4rem;
  margin: 0;
  text-shadow: 0 0 6px var(--color-accent-yellow);
}

.top-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  justify-content: space-between;
}

.search-input {
  flex-grow: 1;
  max-width: 360px;
  padding: 0.5rem 1rem;
  border: 1px solid var(--divider);
  border-radius: 6px;
  background-color: var(--color-bg-secondary);
  color: var(--color-text-light);
  font-family: var(--font-mono);
}

#pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
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
