<!-- Transactions.vue - View and manage transactions using tabbed layout. -->
<template>
  <TabbedPageLayout
    class="transactions-page"
    :tabs="tabs"
    v-model="activeTab"
    padding="px-4 sm:px-6 lg:px-8 py-8"
  >
    <!-- Header -->
    <template #header>
      <PageHeader :icon="CreditCard">
        <template #title>Transactions</template>
        <template #subtitle>View and manage your transactions</template>
      </PageHeader>
    </template>
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

    <!-- Filter Controls -->
    <Card class="p-6">
      <div class="flex flex-wrap items-center gap-4">
        <DateRangeSelector
          :start-date="startDate"
          :end-date="endDate"
          disable-zoom
          @update:startDate="startDate = $event"
          @update:endDate="endDate = $event"
        />
        <AccountFilter v-model="accountFilter" />
        <TypeSelector v-model="txType" />
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


    <!-- Activity Tab -->
    <template #Activity>
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
      <div
        v-if="!searchQuery"
        id="pagination-controls"
        class="flex items-center justify-center gap-4 mt-4"
      >
        <UiButton variant="outline" @click="changePage(-1)" :disabled="currentPage === 1"
          >Prev</UiButton
        >
        <span class="text-muted">Page {{ currentPage }} of {{ totalPages }}</span>
        <UiButton variant="primary" @click="changePage(1)" :disabled="currentPage >= totalPages"
          >Next</UiButton
        >
      </div>
    </template>

    <!-- Recurring Tab -->
    <template #Recurring>
      <Card class="p-6 space-y-4">
        <h2 class="text-2xl font-bold">Recurring Transactions</h2>
        <RecurringTransactionSection ref="recurringFormRef" provider="plaid" />
      </Card>
    </template>

    <!-- Scanner Tab -->
    <template #Scanner>
      <Card class="p-6">
        <InternalTransferScanner />
      </Card>
    </template>
  </TabbedPageLayout>
</template>

<script>
// View for listing and managing transactions with tabbed layout and paging.
// Editing is restricted to date, amount, description, category and merchant name;
// account identifiers and provider metadata remain read-only.
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTransactions } from '@/composables/useTransactions.js'
import UpdateTransactionsTable from '@/components/tables/UpdateTransactionsTable.vue'
import RecurringTransactionSection from '@/components/recurring/RecurringTransactionSection.vue'
import AccountActionsSidebar from '@/components/transactions/AccountActionsSidebar.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import UiButton from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import { CreditCard } from 'lucide-vue-next'
import TabbedPageLayout from '@/components/layout/TabbedPageLayout.vue'
import InternalTransferScanner from '@/components/transactions/InternalTransferScanner.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'
import AccountFilter from '@/components/AccountFilter.vue'
import TypeSelector from '@/components/TypeSelector.vue'

export default {
  name: 'TransactionsView',
  components: {
    UpdateTransactionsTable,
    RecurringTransactionSection,
    AccountActionsSidebar,
    PageHeader,
    UiButton,
    Card,
    TabbedPageLayout,
    InternalTransferScanner,
    DateRangeSelector,
    AccountFilter,
    TypeSelector,
  },
  setup() {
    const route = useRoute()
    const txidParam = route.query?.txid
    const initialPageSize = txidParam ? 250 : 10
    const startDate = ref('')
    const endDate = ref('')
    const accountFilter = ref('')
    const txType = ref('')

    const filters = computed(() => {
      const f = {}
      if (startDate.value) f.start_date = startDate.value
      if (endDate.value) f.end_date = endDate.value
      if (accountFilter.value) f.account_ids = [accountFilter.value]
      if (txType.value) f.tx_type = txType.value
      return f
    })

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
      filters,
    )

    const recurringFormRef = ref(null)
    const tabs = ['Activity', 'Recurring', 'Scanner']
    const activeTab = ref('Activity')

    function prefillRecurringFromTransaction(tx) {
      if (recurringFormRef.value) {
        recurringFormRef.value.transactionId = tx.transaction_id || ''
        recurringFormRef.value.description = tx.description || ''
        recurringFormRef.value.amount = parseFloat(tx.amount) || 0
        recurringFormRef.value.notes = tx.notes || ''
        recurringFormRef.value.showForm = true
      }
    }

    onMounted(() => {
      if (txidParam) {
        searchQuery.value = String(txidParam)
      }
    })

    return {
      tabs,
      activeTab,
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
      CreditCard,
      startDate,
      endDate,
      accountFilter,
      txType,
    }
  },
}
</script>
