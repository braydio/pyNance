<!-- Transactions.vue - View and manage transactions. -->
<template>
  <BasePageLayout class="transactions-page" gap="gap-8" padding="px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <PageHeader>
      <template #icon>
        <CreditCard class="w-6 h-6" />
      </template>
      <template #title>Transactions</template>
      <template #subtitle>View and manage your transactions</template>
      <template #actions>
        <UiButton variant="outline">Import</UiButton>
      </template>
    </PageHeader>

    <!-- Top Controls -->
    <Card class="p-6">
      <div class="grid gap-4 md:grid-cols-2">
        <ImportFileSelector />
        <input v-model="searchQuery" type="text" placeholder="Search transactions..." class="input w-full" />
      </div>
    </Card>

    <!-- Main Table -->
    <Card class="p-6 space-y-4">
      <h2 class="text-2xl font-bold">Recent Transactions</h2>
      <transition name="fade-in-up" mode="out-in">
        <UpdateTransactionsTable :key="currentPage" :transactions="filteredTransactions" :sort-key="sortKey"
          :sort-order="sortOrder" @sort="setSort"
          @editRecurringFromTransaction="prefillRecurringFromTransaction" />
      </transition>
    </Card>

    <!-- Pagination -->
    <div id="pagination-controls" class="flex items-center justify-center gap-4">
      <UiButton variant="outline" @click="changePage(-1)" :disabled="currentPage === 1">Prev</UiButton>
      <span class="text-muted">Page {{ currentPage }} of {{ totalPages }}</span>
      <UiButton variant="primary" @click="changePage(1)" :disabled="currentPage >= totalPages">Next</UiButton>
    </div>

    <!-- Internal Transfer Detection -->
    <InternalTransferScanner />

    <!-- Recurring Transactions -->
    <Card class="p-6 space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold">Recurring Transactions</h2>
        <UiButton variant="outline" @click="showRecurring = !showRecurring">
          {{ showRecurring ? 'Hide' : 'Show' }}
        </UiButton>
      </div>
      <transition name="accordion">
        <div v-if="showRecurring" class="mt-4">
          <RecurringTransactionSection ref="recurringFormRef" provider="plaid" />
        </div>
      </transition>
    </Card>
  </BasePageLayout>
</template>

<script>
// View for listing and managing transactions with themed layout and paging.
// Editing is restricted to date, amount, description, category and merchant name;
// account identifiers and provider metadata remain read-only.
import { ref } from 'vue'
import { useTransactions } from '@/composables/useTransactions.js'
import UpdateTransactionsTable from '@/components/tables/UpdateTransactionsTable.vue'
import RecurringTransactionSection from '@/components/recurring/RecurringTransactionSection.vue'
import ImportFileSelector from '@/components/forms/ImportFileSelector.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import UiButton from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import { CreditCard } from 'lucide-vue-next'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import InternalTransferScanner from '@/components/transactions/InternalTransferScanner.vue'

export default {
  name: 'TransactionsView',
  components: {
    UpdateTransactionsTable,
    RecurringTransactionSection,
    ImportFileSelector,
    PageHeader,
    UiButton,
    Card,
    CreditCard,
    BasePageLayout,
    InternalTransferScanner,
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

    const showRecurring = ref(false)
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
      showRecurring,
      recurringFormRef,
      prefillRecurringFromTransaction,
    }
  },
}
</script>
