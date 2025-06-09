<template>
  <div class="transactions-page container space-y-8">
    <!-- Header -->
    <header class="flex-between">
      <div>
        <h1 class="text-3xl font-bold text-[var(--neon-purple)]">Transactions</h1>
        <h3 class="text-muted mb-2">View and manage your transactions</h3>
      </div>
    </header>

    <!-- Top Controls -->
    <div class="flex flex-wrap justify-between items-end gap-4">
      <ImportFileSelector class="flex-1 min-w-[250px]" />
      <input v-model="searchQuery" type="text" placeholder="Search transactions..."
        class="input flex-1 md:flex-none md:w-64" />
    </div>

    <!-- Main Table -->
    <div class="card overflow-x-auto">
      <UpdateTransactionsTable :transactions="filteredTransactions" :sort-key="sortKey" :sort-order="sortOrder"
        @sort="setSort" @editRecurringFromTransaction="prefillRecurringFromTransaction" />
    </div>

    <!-- Pagination -->
    <div id="pagination-controls" class="flex items-center justify-center gap-4">
      <button class="btn" @click="changePage(-1)" :disabled="currentPage === 1">Prev</button>
      <span class="text-muted">Page {{ currentPage }} of {{ totalPages }}</span>
      <button class="btn" @click="changePage(1)" :disabled="currentPage >= totalPages">Next</button>
    </div>

    <!-- Recurring Transactions -->
    <RecurringTransactionSection ref="recurringFormRef" provider="plaid" class="card" />
  </div>
</template>

<script>
import { ref } from 'vue'
import { useTransactions } from '@/composables/useTransactions.js'
import UpdateTransactionsTable from '@/components/tables/UpdateTransactionsTable.vue'
import RecurringTransactionSection from '@/components/recurring/RecurringTransactionSection.vue'
import ImportFileSelector from '@/components/forms/ImportFileSelector.vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import CategoryBreakdownChart from '@/components/charts/CategoryBreakdownChart.vue'

export default {
  name: 'Transactions',
  components: {
    UpdateTransactionsTable,
    RecurringTransactionSection,
    ImportFileSelector,
    DailyNetChart,
    CategoryBreakdownChart,
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
      prefillRecurringFromTransaction,
    }
  },
}
</script>
