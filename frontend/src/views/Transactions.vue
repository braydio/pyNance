<!-- Transactions.vue - View and manage transactions using tabbed layout. -->
<template>
  <TabbedPageLayout
    class="transactions-page text-slate-900"
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
    <Card class="p-6 rounded-3xl card-surface">
      <div class="flex items-center justify-between">
        <div>
          <p class="eyebrow">Automation</p>
          <h2 class="text-xl font-semibold text-slate-900">Internal Transfer Scanner</h2>
          <p class="text-sm text-slate-600">Quickly spot and link matching transfers.</p>
        </div>
        <button class="btn btn-outline px-3 py-1 text-sm" @click="toggleScanner">
          {{ showScanner ? 'Hide' : 'Show' }}
        </button>
      </div>
      <div class="mt-4" v-if="showScanner">
        <InternalTransferScanner />
      </div>
    </Card>

    <!-- Top Controls -->
    <Card
      v-if="showControls"
      id="top-controls"
      class="p-6 rounded-3xl card-surface space-y-4"
    >
      <div class="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-4">
        <div class="space-y-1">
          <p class="eyebrow">Controls</p>
          <h3 class="text-lg font-semibold text-slate-900">Import &amp; quick search</h3>
          <p class="text-sm text-slate-600">Upload transactions and instantly narrow the view.</p>
        </div>
        <span class="pill">Transactions</span>
      </div>
      <div class="grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(260px,1fr)]">
        <div class="rounded-2xl border border-dashed border-slate-200 bg-white/90 p-4 shadow-inner">
          <ImportFileSelector />
        </div>
        <div class="relative rounded-2xl border border-dashed border-slate-200 bg-white/80 shadow-inner">
          <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            <Search class="w-4 h-4" />
          </span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search transactions..."
            class="input w-full border-none bg-transparent pl-10 pr-4 py-3 focus:ring-2 focus:ring-[var(--color-accent-purple)] text-slate-900"
          />
        </div>
      </div>
    </Card>

    <!-- Filter Controls -->
    <Card class="p-6 rounded-3xl card-surface space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="eyebrow">Filters</p>
          <h3 class="text-lg font-semibold text-slate-900">Refine the transaction view</h3>
          <p class="text-sm text-slate-600">Adjust time range, account, and transaction type.</p>
        </div>
        <div class="flex items-center gap-2 text-xs text-slate-600">
          <span class="h-2 w-2 rounded-full bg-[var(--color-accent-purple)] shadow-glow"></span>
          Live updates
        </div>
      </div>
      <div class="grid w-full gap-3 md:grid-cols-3">
        <div class="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-inner">
          <DateRangeSelector
            :start-date="startDate"
            :end-date="endDate"
            disable-zoom
            @update:startDate="startDate = $event"
            @update:endDate="endDate = $event"
          />
        </div>
        <div class="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-inner">
          <AccountFilter v-model="accountFilter" />
        </div>
        <div class="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-inner">
          <TypeSelector v-model="txType" />
        </div>
      </div>
    </Card>

    <!-- Main Table -->
    <Card class="p-6 space-y-4 rounded-3xl card-surface">
      <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold text-slate-900">Recent Transactions</h2>
        <span class="pill pill-subtle">Updated feed</span>
      </div>
      <transition name="fade-in-up" mode="out-in">
        <SkeletonCard v-if="isLoading" key="loading" />
        <RetryError
          v-else-if="error"
          key="error"
          :message="errorMessage"
          @retry="fetchTransactions"
        />
        <UpdateTransactionsTable
          v-else
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
      <Card class="p-6 space-y-4 rounded-3xl card-surface">
        <h2 class="text-2xl font-bold text-slate-900">Recent Transactions</h2>
        <transition name="fade-in-up" mode="out-in">
          <SkeletonCard v-if="isLoading" key="loading-activity" />
          <RetryError
            v-else-if="error"
            key="error-activity"
            :message="errorMessage"
            @retry="fetchTransactions"
          />
          <UpdateTransactionsTable
            v-else
            :key="currentPage"
            :transactions="filteredTransactions"
            :sort-key="sortKey"
            :sort-order="sortOrder"
            @sort="setSort"
            @editRecurringFromTransaction="prefillRecurringFromTransaction"
          />
        </transition>
      </Card>
      <PaginationControls
        v-if="!searchQuery && !error"
        id="pagination-controls"
        :current-page="currentPage"
        :total-pages="totalPages"
        :page-size="initialPageSize"
        :total-items="totalCount"
        @change-page="setPage"
      />
    </template>

    <!-- Recurring Tab -->
    <template #Recurring>
      <Card class="p-6 space-y-4 rounded-3xl card-surface">
        <h2 class="text-2xl font-bold text-slate-900">Recurring Transactions</h2>
        <RecurringTransactionSection ref="recurringFormRef" provider="plaid" />
      </Card>
    </template>

    <!-- Scanner Tab -->
    <template #Scanner>
      <Card class="p-6 rounded-3xl card-surface">
        <InternalTransferScanner />
      </Card>
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
import PageHeader from '@/components/ui/PageHeader.vue'
import UiButton from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import { CreditCard, Search } from 'lucide-vue-next'
import TabbedPageLayout from '@/components/layout/TabbedPageLayout.vue'
import InternalTransferScanner from '@/components/transactions/InternalTransferScanner.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'
import AccountFilter from '@/components/AccountFilter.vue'
import TypeSelector from '@/components/TypeSelector.vue'
import SkeletonCard from '@/components/ui/SkeletonCard.vue'
import RetryError from '@/components/errors/RetryError.vue'
import PaginationControls from '@/components/tables/PaginationControls.vue'

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
    DateRangeSelector,
    AccountFilter,
    TypeSelector,
    SkeletonCard,
    RetryError,
    PaginationControls,
    Search,
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
    const showScanner = ref(false)
    const showControls = ref(true)

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
    syncQueryParam(startDate, ['start_date'])
    syncQueryParam(endDate, ['end_date'])
    syncQueryParam(txType, ['tx_type', 'type'])

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
      totalCount,
      filteredTransactions,
      sortKey,
      sortOrder,
      setSort,
      setPage,
    } = useTransactions(initialPageSize, promotedTransactionId, filters)

    /**
     * Provide a stable, human-readable message for retryable errors.
     *
     * @returns {string}
     */
    const errorMessage = computed(
      () => error.value?.message || 'Unable to load transactions. Please try again.',
    )

    const recurringFormRef = ref(null)
    const tabs = ['Activity', 'Recurring', 'Scanner']
    const activeTab = ref('Activity')

    /**
     * Toggle the visibility of the internal transfer scanner widget.
     */
    function toggleScanner() {
      showScanner.value = !showScanner.value
    }

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

    return {
      tabs,
      activeTab,
      searchQuery,
      currentPage,
      totalPages,
      totalCount,
      initialPageSize,
      filteredTransactions,
      sortKey,
      sortOrder,
      setSort,
      setPage,
      recurringFormRef,
      prefillRecurringFromTransaction,
      CreditCard,
      startDate,
      endDate,
      accountFilter,
      txType,
      showScanner,
      toggleScanner,
      showControls,
    }
  },
}
</script>

<style scoped>
@reference "tailwindcss";
.transactions-page {
  @apply min-h-screen;
  background: linear-gradient(135deg, #e6e9f0 0%, #f3f5f9 38%, #e9ecf8 100%);
}

.card-surface {
  @apply border border-slate-200 bg-white/90 shadow-[0_18px_60px_rgba(15,23,42,0.08)];
}

.eyebrow {
  @apply text-xs font-semibold uppercase tracking-[0.12em] text-slate-500;
}

.pill {
  @apply inline-flex items-center gap-2 px-3 py-1 text-xs font-semibold text-slate-700 bg-slate-100 border border-slate-200 rounded-full shadow-sm;
}

.pill-subtle {
  @apply bg-indigo-50 text-indigo-700 border-indigo-100;
}

.shadow-glow {
  box-shadow: 0 0 0 6px rgba(157, 121, 214, 0.12);
}

.transactions-page :deep(.input) {
  @apply bg-white text-slate-900 border border-slate-200 rounded-xl;
}

.transactions-page :deep(.input:focus) {
  @apply ring-2 ring-indigo-200 outline-none;
}
</style>
