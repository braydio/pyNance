<!-- Transactions.vue - View and manage transactions using tabbed layout. -->
<template>
  <TabbedPageLayout
    class="transactions-page"
    :tabs="tabs"
    v-model="activeTab"
    padding="px-4 sm:px-6 lg:px-8 py-8"
    sidebar-width="w-72 xl:w-80"
  >
    <!-- Header -->
    <template #header>
      <PageHeader :icon="CreditCard">
        <template #title>Transactions</template>
        <template #subtitle>View and manage your transactions</template>
      </PageHeader>
    </template>
    <!-- Activity Tab -->
    <template #Activity>
      <div class="space-y-4" data-testid="transactions-activity-panel">
        <Card class="p-6 space-y-4">
          <div class="flex items-center justify-between gap-4">
            <h2 class="text-2xl font-bold">Recent Transactions</h2>
          </div>
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
          class="flex items-center justify-center gap-4"
          data-testid="transactions-pagination"
        >
          <UiButton variant="outline" @click="changePage(-1)" :disabled="currentPage === 1"
            >Prev</UiButton
          >
          <span class="text-muted">Page {{ currentPage }} of {{ totalPages }}</span>
          <UiButton variant="primary" @click="changePage(1)" :disabled="currentPage >= totalPages"
            >Next</UiButton
          >
        </div>
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
      <Card class="p-6" data-testid="scanner-panel">
        <InternalTransferScanner />
      </Card>
    </template>

    <template #sidebar>
      <AccountActionsSidebar
        v-model:search="searchQuery"
        v-model:start-date="startDate"
        v-model:end-date="endDate"
        v-model:account-id="accountFilter"
        v-model:tx-type="txType"
        @open-scanner="openScannerTab"
      />
    </template>
  </TabbedPageLayout>
</template>

<script>
// View for listing and managing transactions with tabbed layout and paging.
// Editing is restricted to date, amount, description, category and merchant name;
// account identifiers and provider metadata remain read-only.
import { ref, onMounted, computed, watch } from 'vue'
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

export default {
  name: 'TransactionsView',
  components: {
    UpdateTransactionsTable,
    RecurringTransactionSection,
    PageHeader,
    UiButton,
    Card,
    TabbedPageLayout,
    InternalTransferScanner,
    AccountActionsSidebar,
  },
  setup() {
    const route = useRoute()

    /**
     * Normalize a vue-router query parameter to a single string value.
     *
     * @param {string | string[] | null | undefined} value
     * @returns {string}
     */
    function coerceQueryValue(value) {
      if (Array.isArray(value)) {
        return value[0] ?? ''
      }
      if (value == null) return ''
      return String(value)
    }

    const txidParam = coerceQueryValue(route.query?.txid)
    const initialPageSize = txidParam ? 250 : 10
    const startDate = ref('')
    const endDate = ref('')
    const initialAccountId = coerceQueryValue(route.query?.account_id)
    const accountFilter = ref(initialAccountId)
    const txType = ref('')
    const initialPromoteId = coerceQueryValue(route.query?.promote || route.query?.promote_txid)
    const promotedTransactionId = ref(initialPromoteId)

    /**
     * Keep the provided ref synchronized with vue-router query parameters.
     *
     * @param {import('vue').Ref<string>} targetRef - Ref to synchronize.
     * @param {string[]} keys - Query parameter keys ordered by preference.
     */
    function syncQueryParam(targetRef, keys) {
      watch(
        () => keys.map((key) => route.query?.[key]),
        (values) => {
          let nextValue = ''
          for (const value of values) {
            const normalized = coerceQueryValue(value)
            if (normalized) {
              nextValue = normalized
              break
            }
          }

          if (nextValue !== targetRef.value) {
            targetRef.value = nextValue
          }
        },
        { immediate: true },
      )
    }

    syncQueryParam(accountFilter, ['account_id'])
    syncQueryParam(promotedTransactionId, ['promote', 'promote_txid'])

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
    } = useTransactions(initialPageSize, promotedTransactionId, filters)

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
        searchQuery.value = txidParam
      }
    })

    function openScannerTab() {
      activeTab.value = 'Scanner'
    }

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
      openScannerTab,
    }
  },
}
</script>
