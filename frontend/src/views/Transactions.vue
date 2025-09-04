<!-- Transactions.vue - View and manage transactions. -->
<template>
  <BasePageLayout class="transactions-page" gap="gap-8" padding="px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <PageHeader :icon="CreditCard">
      <template #title>Transactions</template>
      <template #subtitle>View and manage your transactions</template>
      <template #actions>
        <UiButton
          id="toggle-controls"
          variant="outline"
          @click="toggleControls"
        >
          {{ showControls ? 'Hide Controls' : 'Show Controls' }}
        </UiButton>
      </template>
    </PageHeader>

    <!-- Internal Transfer Scanner (moved to top) -->
    <Card class="p-6 rounded-2xl">
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-semibold">Internal Transfer Scanner</h2>
        <button class="btn btn-outline px-3 py-1 text-sm" @click="toggleScanner">
          {{ showScanner ? 'Hide' : 'Show' }}
        </button>
      </div>
      <div class="mt-4" v-if="showScanner">
        <InternalTransferScanner />
      </div>
    </Card>

    <!-- Top Controls -->
    <Card v-if="showControls" id="top-controls" class="p-6">
      <div class="grid gap-4 md:grid-cols-2">
        <ImportFileSelector />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search transactions..."
          class="input w-full"
        />
      </div>
    </Card>

    <!-- Main Table -->
    <Card class="p-6 space-y-4">
      <h2 class="text-2xl font-bold">Recent Transactions</h2>
      <transition name="fade-in-up" mode="out-in">
        <UpdateTransactionsTable
          :key="currentPage"
          :transactions="filteredTransactions"
          :sort-key="sortKey"
          :sort-order="sortOrder"
          @sort="setSort"
          @editRecurringFromTransaction="prefillRecurringFromTransaction"
        />
      </transition>
    </Card>

    <!-- Pagination -->
    <div
      v-if="!searchQuery"
      id="pagination-controls"
      class="flex items-center justify-center gap-4"
    >
      <UiButton variant="outline" @click="changePage(-1)" :disabled="currentPage === 1"
        >Prev</UiButton
      >
      <span class="text-muted">Page {{ currentPage }} of {{ totalPages }}</span>
      <UiButton variant="primary" @click="changePage(1)" :disabled="currentPage >= totalPages"
        >Next</UiButton
      >
    </div>

    <!-- Removed: Scanner was moved above -->

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
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
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
    BasePageLayout,
    InternalTransferScanner,
  },
  setup() {
    const route = useRoute()
    const txidParam = route.query?.txid
    // If deep-linking to a transaction, use a larger initial page size to improve hit rate
    const initialPageSize = txidParam ? 250 : 10
    const {
      searchQuery,
      currentPage,
      totalPages,
      filteredTransactions,
      changePage,
      sortKey,
      sortOrder,
      setSort,
    } = useTransactions(
      initialPageSize,
      ref(route.query?.promote || route.query?.promote_txid || ''),
    )

    const showControls = ref(false)
    const showScanner = ref(false)
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

    function toggleScanner() {
      showScanner.value = !showScanner.value
    }

    /** Toggle visibility of import/search controls. */
    function toggleControls() {
      showControls.value = !showControls.value
    }

    // Apply deep-link search if present
    onMounted(() => {
      if (txidParam) {
        searchQuery.value = String(txidParam)
      }
    })

    return {
      searchQuery,
      currentPage,
      totalPages,
      filteredTransactions,
      changePage,
      sortKey,
      sortOrder,
      setSort,
      showControls,
      showScanner,
      toggleScanner,
      showRecurring,
      toggleControls,
      recurringFormRef,
      prefillRecurringFromTransaction,
      CreditCard,
    }
  },
}
</script>
