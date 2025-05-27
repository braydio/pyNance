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
