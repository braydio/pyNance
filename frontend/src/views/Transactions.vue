<!-- Transactions.vue - View and manage transactions using tabbed layout. -->
<template>
  <TabbedPageLayout class="transactions-page" :tabs="tabs" v-model="activeTab">
    <!-- Header -->
    <template #header>
      <PageHeader :icon="CreditCard">
        <template #title>Transactions</template>
        <template #subtitle>Search, review, and export your activity</template>
      </PageHeader>
    </template>
    <!-- Activity Tab -->
    <template #Activity>
      <!-- One compact toolbar: search + filters + import + export -->
      <div id="activity-toolbar" class="activity-toolbar surface-quiet p-3 md:p-4">
        <div class="activity-toolbar__row">
          <label class="activity-toolbar__search" for="transactions-search">
            <span class="sr-only">Search transactions</span>
            <Search class="activity-toolbar__search-icon w-4 h-4" aria-hidden="true" />
            <input
              id="transactions-search"
              v-model="searchQuery"
              type="text"
              placeholder="Search transactions"
              class="input ui-control-input w-full pl-9 pr-3 py-2 search-input"
            />
          </label>
          <button
            type="button"
            class="btn btn-outline activity-toolbar__filters-toggle"
            data-testid="filters-toggle"
            aria-controls="activity-filters"
            :aria-expanded="filtersOpen"
            @click="filtersOpen = !filtersOpen"
          >
            Filters<span v-if="activeFilterChips.length"> ({{ activeFilterChips.length }})</span>
          </button>
          <button
            v-if="hasActiveFilters || searchQuery"
            type="button"
            class="btn btn-outline"
            data-testid="clear-search-filters"
            @click="clearSearchAndFilters"
          >
            Clear
          </button>
          <button
            type="button"
            class="btn btn-outline"
            data-testid="import-toggle"
            aria-controls="activity-import"
            :aria-expanded="importOpen"
            @click="importOpen = !importOpen"
          >
            Import
          </button>
        </div>
        <div
          id="activity-filters"
          class="activity-toolbar__filters"
          :class="{ 'is-open': filtersOpen }"
          data-testid="activity-filters"
        >
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
        <div v-if="importOpen" id="activity-import" class="activity-toolbar__import">
          <ImportFileSelector />
        </div>
      </div>

      <!-- Table is the dominant surface -->
      <Card class="p-4 md:p-6 space-y-3 ui-radius-3 card-surface">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <h2 class="section-title">
            Transactions
            <span v-if="!isLoading && !error" class="result-count" data-testid="result-count">
              · {{ filterSummary.transactionCount }} shown
            </span>
          </h2>
          <button
            class="pill md:text-sm"
            data-testid="transactions-export-csv-activity"
            :disabled="isExporting || isLoading"
            @click="exportFilteredTransactionsCsv"
          >
            {{ isExporting ? 'Exporting CSV...' : 'Export CSV (All Filtered Rows)' }}
          </button>
        </div>
        <div
          v-if="hasActiveFilters && !isLoading && !error"
          class="filter-summary"
          data-testid="filter-summary"
        >
          <span class="filter-summary__total">
            Total {{ formatCurrency(filterSummary.totalAmount) }}
          </span>
          <ul class="filter-summary__chips" aria-label="Active filters">
            <li v-for="chip in activeFilterChips" :key="chip" class="pill pill-subtle">
              {{ chip }}
            </li>
          </ul>
          <button
            type="button"
            class="filter-summary__clear"
            data-testid="clear-filters"
            @click="clearFilters"
          >
            Clear filters
          </button>
        </div>
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
            :transactions="filteredTransactions"
            :current-page="currentPage"
            :page-size="initialPageSize"
            :sort-key="sortKey"
            :sort-order="sortOrder"
            :auto-edit-transaction-id="targetTransactionId"
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
      <Card class="p-6 space-y-4 ui-radius-3 card-surface">
        <h2 class="text-2xl font-bold text-[var(--color-text-light)]">Recurring Transactions</h2>
        <RecurringTransactionSection ref="recurringFormRef" provider="plaid" />
      </Card>
    </template>

    <!-- Scanner Tab -->
    <template #Scanner>
      <Card class="p-6 ui-radius-3 card-surface">
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
import { fetchTransactions as fetchTransactionsApi } from '@/api/transactions'
import UpdateTransactionsTable from '@/components/tables/UpdateTransactionsTable.vue'
import RecurringTransactionSection from '@/components/recurring/RecurringTransactionSection.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import Card from '@/components/ui/Card.vue'
import { CreditCard, Search } from 'lucide-vue-next'
import TabbedPageLayout from '@/components/layout/TabbedPageLayout.vue'
import InternalTransferScanner from '@/components/transactions/InternalTransferScanner.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'
import AccountFilter from '@/components/AccountFilter.vue'
import TypeSelector from '@/components/TypeSelector.vue'
import ImportFileSelector from '@/components/forms/ImportFileSelector.vue'
import SkeletonCard from '@/components/ui/SkeletonCard.vue'
import RetryError from '@/components/errors/RetryError.vue'
import PaginationControls from '@/components/tables/PaginationControls.vue'

export default {
  name: 'TransactionsView',
  components: {
    UpdateTransactionsTable,
    RecurringTransactionSection,
    PageHeader,
    Card,
    TabbedPageLayout,
    InternalTransferScanner,
    DateRangeSelector,
    AccountFilter,
    TypeSelector,
    ImportFileSelector,
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
    const initialPageSize = 10
    const startDate = ref('')
    const endDate = ref('')
    const initialAccountId = coerceQueryValue(route.query?.account_id)
    const accountFilter = ref(initialAccountId)
    const txType = ref('')
    const initialPromoteId = coerceQueryValue(route.query?.promote || route.query?.promote_txid)
    const promotedTransactionId = ref(initialPromoteId)
    const targetTransactionId = ref(txidParam)
    const filtersOpen = ref(false)
    const importOpen = ref(false)
    const isExporting = ref(false)

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
      isLoading,
      error,
      fetchTransactions,
    } = useTransactions(initialPageSize, promotedTransactionId, filters, {
      includeRunningBalance: true,
      targetTransactionIdRef: targetTransactionId,
    })

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
     * Determine whether a top-level transaction filter is currently active.
     *
     * @returns {boolean}
     */
    const hasActiveFilters = computed(() =>
      Boolean(startDate.value || endDate.value || accountFilter.value || txType.value),
    )

    /**
     * Convert a transaction amount value to a safe numeric value.
     *
     * @param {number | string | null | undefined} amount
     * @returns {number}
     */
    function toNumericAmount(amount) {
      const parsed = Number(amount)
      return Number.isFinite(parsed) ? parsed : 0
    }

    /**
     * Build summary metrics for currently filtered transactions.
     *
     * @returns {{transactionCount: number, totalAmount: number, uniqueCounts: Record<string, number>}}
     */
    const filterSummary = computed(() => {
      const transactions = Array.isArray(filteredTransactions.value)
        ? filteredTransactions.value
        : []
      const uniqueCategories = new Set()
      const uniqueMerchants = new Set()
      const uniqueAccounts = new Set()
      const uniqueInstitutions = new Set()

      const totalAmount = transactions.reduce((sum, tx) => {
        if (tx?.category) uniqueCategories.add(tx.category)
        if (tx?.merchant_name) uniqueMerchants.add(tx.merchant_name)
        if (tx?.account_name) uniqueAccounts.add(tx.account_name)
        if (tx?.institution_name) uniqueInstitutions.add(tx.institution_name)
        return sum + toNumericAmount(tx?.amount)
      }, 0)

      return {
        transactionCount: transactions.length,
        totalAmount,
        uniqueCounts: {
          categories: uniqueCategories.size,
          merchants: uniqueMerchants.size,
          accounts: uniqueAccounts.size,
          institutions: uniqueInstitutions.size,
        },
      }
    })

    /**
     * Format a numeric amount as a localized USD string.
     *
     * @param {number} value
     * @returns {string}
     */
    function formatCurrency(value) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(value)
    }

    /** Human-readable chips for each active top-level filter. */
    const activeFilterChips = computed(() => {
      const chips = []
      if (startDate.value || endDate.value) {
        chips.push(`${startDate.value || '…'} – ${endDate.value || '…'}`)
      }
      if (accountFilter.value) chips.push('Account')
      if (txType.value) chips.push(`Type: ${txType.value}`)
      return chips
    })

    /** Reset all top-level filters (search is cleared separately by the user). */
    /** Reset the search box together with every filter (toolbar "Clear"). */
    function clearSearchAndFilters() {
      searchQuery.value = ''
      clearFilters()
    }

    function clearFilters() {
      startDate.value = ''
      endDate.value = ''
      accountFilter.value = ''
      txType.value = ''
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

    /**
     * Convert rows to CSV-safe text.
     *
     * @param {Array<Record<string, unknown>>} rows
     * @returns {string}
     */
    function toCsv(rows) {
      const columns = [
        ['transaction_id', 'Transaction ID'],
        ['date', 'Date'],
        ['amount', 'Amount'],
        ['description', 'Description'],
        ['category', 'Category'],
        ['merchant_name', 'Merchant'],
        ['account_name', 'Account Name'],
        ['institution_name', 'Institution'],
        ['subtype', 'Subtype'],
        ['running_balance', 'Running Balance'],
      ]

      const escapeCell = (value) => {
        if (value == null) return '""'
        const text = String(value).replace(/"/g, '""')
        return `"${text}"`
      }

      const lines = [columns.map(([, header]) => escapeCell(header)).join(',')]
      rows.forEach((row) => {
        const line = columns.map(([key]) => escapeCell(row[key])).join(',')
        lines.push(line)
      })
      return lines.join('\n')
    }

    /**
     * Download all transactions matching the active server-side filters.
     * This bypasses dashboard pagination by paging through the full result set.
     */
    async function exportFilteredTransactionsCsv() {
      if (isExporting.value) return
      isExporting.value = true

      try {
        const exportPageSize = 500
        const activeFilters = {
          ...(filters.value || {}),
          include_running_balance: true,
        }
        let page = 1
        let expectedTotal = 0
        const allRows = []

        let shouldContinue = true
        while (shouldContinue) {
          const response = await fetchTransactionsApi({
            ...activeFilters,
            page,
            page_size: exportPageSize,
          })
          const batch = Array.isArray(response?.transactions) ? response.transactions : []
          expectedTotal = Number(response?.total || 0)
          allRows.push(...batch)

          if (!batch.length) {
            shouldContinue = false
          } else if (expectedTotal > 0 && allRows.length >= expectedTotal) {
            shouldContinue = false
          } else {
            page += 1
          }
        }

        const search = searchQuery.value.trim().toLowerCase()
        const rowsForExport = !search
          ? allRows
          : allRows.filter((tx) =>
              [
                tx.transaction_id,
                tx.date,
                tx.description,
                tx.category,
                tx.merchant_name,
                tx.account_name,
                tx.institution_name,
              ].some((value) =>
                String(value || '')
                  .toLowerCase()
                  .includes(search),
              ),
            )

        const csv = toCsv(rowsForExport)
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
        const url = URL.createObjectURL(blob)
        const timestamp = new Date().toISOString().replace(/[:]/g, '-').replace(/\..+/, '')
        const link = document.createElement('a')
        link.href = url
        link.download = `transactions-export-${timestamp}.csv`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      } catch (err) {
        console.error('Failed to export filtered transactions', err)
        window.alert('Failed to export transactions CSV. Please try again.')
      } finally {
        isExporting.value = false
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
      isLoading,
      error,
      fetchTransactions,
      errorMessage,
      recurringFormRef,
      prefillRecurringFromTransaction,
      CreditCard,
      startDate,
      endDate,
      accountFilter,
      txType,
      targetTransactionId,
      filtersOpen,
      importOpen,
      activeFilterChips,
      clearFilters,
      isExporting,
      exportFilteredTransactionsCsv,
      hasActiveFilters,
      clearSearchAndFilters,
      filterSummary,
      formatCurrency,
    }
  },
}
</script>

<style scoped>
@reference "tailwindcss";
.transactions-page {
  @apply min-h-screen;
  background: var(--page-bg);
  color: var(--color-text-light);
}

.card-surface {
  background: var(--color-bg-secondary);
  border: 1px solid var(--divider);
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.18);
}

.eyebrow {
  @apply text-xs font-semibold uppercase tracking-[0.12em];
  color: var(--color-text-muted);
}

.pill {
  @apply inline-flex items-center gap-2 px-3 py-1 text-sm font-semibold rounded-full shadow-sm;
  color: var(--color-text-light);
  background: var(--color-bg-secondary);
  border: 1px solid var(--divider);
}

.pill-subtle {
  background: rgba(113, 156, 214, 0.16);
  color: var(--text-link);
  border: 1px solid rgba(113, 156, 214, 0.3);
}

.shadow-glow {
  box-shadow: 0 0 0 6px rgba(157, 121, 214, 0.12);
}

.transactions-page :deep(.input) {
  background: var(--input-bg);
  color: var(--color-text-light);
  border: 1px solid var(--divider);
  border-radius: 0.75rem;
}

.transactions-page :deep(.input:focus) {
  outline: none;
  box-shadow: 0 0 0 2px rgba(113, 156, 214, 0.35);
}

.search-input {
  color: var(--color-text-light);
}

.activity-toolbar {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.activity-toolbar__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.activity-toolbar__search {
  position: relative;
  flex: 1 1 14rem;
  min-width: 0;
}

/* Phones: search owns its row; Filters / Import / Clear sit below it. */
@media (max-width: 639px) {
  .activity-toolbar__search {
    flex-basis: 100%;
  }
}

.activity-toolbar__import {
  max-height: min(24rem, 60dvh);
  overflow: auto;
  overscroll-behavior: contain;
}

.activity-toolbar__search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-muted);
}

.activity-toolbar__filters {
  display: none;
  gap: 0.75rem;
  flex-direction: column;
}

.activity-toolbar__filters.is-open {
  display: flex;
}

.result-count {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-muted);
}

.filter-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.75rem;
  font-size: 0.875rem;
}

.filter-summary__total {
  font-weight: 600;
}

.filter-summary__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  list-style: none;
  padding: 0;
  margin: 0;
}

.filter-summary__clear {
  text-decoration: underline;
  color: var(--color-text-muted);
}

@media (min-width: 768px) {
  .activity-toolbar__filters {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    align-items: flex-end;
  }

  .activity-toolbar__filters-toggle {
    display: none;
  }
}

.section-title {
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: var(--color-text-light);
}
</style>
