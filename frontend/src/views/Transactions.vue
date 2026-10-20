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
      <!-- Summary metrics and prioritized review queue (server-side, over ALL matching rows) -->
      <Card class="p-4 md:p-6 ui-radius-3 card-surface">
        <TransactionInsightsPanel
          :insights="insights"
          :loading="insightsLoading"
          :error="insightsError"
          :scope-label="insightsScopeLabel"
          @apply="applyReviewItem"
          @refresh="loadInsights(true)"
        />
      </Card>

      <!-- One compact toolbar: search + period + account + sort + filters + import -->
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
          <label class="activity-toolbar__select">
            <span class="sr-only">Period</span>
            <select v-model="periodPreset" class="input" data-testid="period-preset">
              <option v-for="option in periodOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <AccountFilter v-model="accountFilter" />
          <label class="activity-toolbar__select">
            <span class="sr-only">Sort by</span>
            <select v-model="sortOption" class="input" data-testid="sort-select">
              <option v-for="option in sortOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <button
            type="button"
            class="btn btn-outline activity-toolbar__filters-toggle"
            data-testid="filters-toggle"
            aria-controls="activity-filters"
            :aria-expanded="filtersOpen"
            @click="filtersOpen = !filtersOpen"
          >
            Advanced filters<span v-if="activeFilterChips.length">
              ({{ activeFilterChips.length }})</span
            >
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
              · {{ resultCountLabel }}
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
          v-if="hasAnyFilter && !isLoading && !error"
          class="filter-summary"
          data-testid="filter-summary"
        >
          <div class="filter-summary__scope" data-testid="summary-matching">
            <span class="filter-summary__heading">
              Filtered results · {{ matchingCountLabel }}
            </span>
            <span
              v-if="summaryStatus === 'loading' && !matchingSummary"
              class="filter-summary__note"
            >
              Updating totals…
            </span>
            <template v-else-if="matchingSummary">
              <span class="filter-summary__total" data-testid="summary-income">
                Economic income (excl. transfers) {{ formatCurrency(matchingSummary.income) }}
              </span>
              <span class="filter-summary__total" data-testid="summary-expenses">
                Economic expenses {{ formatCurrency(matchingSummary.expenses) }}
              </span>
              <span class="filter-summary__total" data-testid="summary-refunds">
                Refund adjustments {{ formatCurrency(matchingSummary.refunds) }}
              </span>
              <span
                class="filter-summary__total filter-summary__total--net"
                data-testid="summary-net"
              >
                Economic net {{ formatCurrency(matchingSummary.economic_net) }}
              </span>
              <span v-if="summaryStale" class="filter-summary__note" data-testid="summary-stale">
                Stale: the last refresh failed
              </span>
            </template>
            <span
              v-if="summaryStatus === 'error'"
              class="filter-summary__note"
              data-testid="summary-error"
              role="alert"
            >
              {{ matchingSummary ? 'Totals may be out of date.' : 'Totals unavailable.' }}
              <button type="button" class="filter-summary__retry" @click="refreshSummary">
                Retry
              </button>
            </span>
          </div>
          <div class="filter-summary__page" data-testid="summary-page">
            Page {{ currentPage }} of {{ totalPages }} · {{ pageSubtotal.count }} shown ·
            <span
              :title="'Signed sum of the rows on this page only (money out is negative). This is cash movement, not income or net.'"
            >
              Cash movement (current page) {{ formatCurrency(pageSubtotal.cashMovement) }}
            </span>
          </div>
          <details
            v-if="matchingSummary && movementRows.length"
            class="filter-summary__movement"
            data-testid="summary-movement"
          >
            <summary>Transfers, debt payments and rows to review</summary>
            <ul>
              <li v-for="row in movementRows" :key="row.label">{{ row.label }}: {{ row.value }}</li>
            </ul>
          </details>
          <ul class="filter-summary__chips" aria-label="Active filters">
            <li v-for="chip in scopeChips" :key="chip" class="pill pill-subtle">
              {{ chip }}
            </li>
          </ul>
          <button
            type="button"
            class="filter-summary__clear"
            data-testid="clear-filters"
            @click="clearSearchAndFilters"
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
            :key="tableResetKey"
            :transactions="pageRows"
            :current-page="currentPage"
            :page-size="initialPageSize"
            :sort-key="sortKey"
            :sort-order="sortOrder"
            :auto-edit-transaction-id="targetTransactionId"
            server-filtered
            @update:filters="tableFilters = $event"
            @changed="onTransactionsChanged"
            @sort="setSort"
            @editRecurringFromTransaction="prefillRecurringFromTransaction"
          />
        </transition>
      </Card>
      <PaginationControls
        v-if="!error"
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
        <RecurringTransactionSection ref="recurringFormRef" />
      </Card>
    </template>

    <!-- Transfer Review Tab (slot id stays `Scanner`) -->
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
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useTransactions } from '@/composables/useTransactions.js'
import { useTransactionSummary } from '@/composables/useTransactionSummary.js'
import { visiblePageSubtotal } from '@/utils/flowSummary.js'
import { fetchTransactions as fetchTransactionsApi } from '@/api/transactions'
import api from '@/services/api'
import { formatDateInput } from '@/composables/useDateRange.js'
import UpdateTransactionsTable from '@/components/tables/UpdateTransactionsTable.vue'
import RecurringTransactionSection from '@/components/recurring/RecurringTransactionSection.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import Card from '@/components/ui/Card.vue'
import { CreditCard, Search } from 'lucide-vue-next'
import TabbedPageLayout from '@/components/layout/TabbedPageLayout.vue'
import InternalTransferScanner from '@/components/transactions/InternalTransferScanner.vue'
import TransactionInsightsPanel from '@/components/transactions/TransactionInsightsPanel.vue'
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
    TransactionInsightsPanel,
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
    // Column and category filters owned by the table component, reported as server parameters.
    const tableFilters = ref({})
    const tableResetKey = ref(0)

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

    /** Server-side ordering across ALL matching rows (not just the loaded page). */
    const sortOptions = [
      { value: 'date_desc', label: 'Newest' },
      { value: 'date_asc', label: 'Oldest' },
      { value: 'spend_desc', label: 'Largest spend' },
      { value: 'amount_desc', label: 'Amount' },
      { value: 'merchant_asc', label: 'Merchant' },
      { value: 'category_asc', label: 'Category' },
    ]
    const sortOption = ref('date_desc')

    const periodOptions = [
      { value: '', label: 'All time' },
      { value: '30d', label: 'Last 30 days' },
      { value: 'mtd', label: 'This month' },
      { value: '90d', label: 'Last 90 days' },
      { value: 'ytd', label: 'Year to date' },
      { value: 'custom', label: 'Custom dates' },
    ]

    /** Inclusive local-calendar dates for a preset. */
    function rangeForPreset(preset, now = new Date()) {
      const end = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const shift = (days) => new Date(end.getFullYear(), end.getMonth(), end.getDate() - days)
      if (preset === '30d') return { start: formatDateInput(shift(29)), end: formatDateInput(end) }
      if (preset === '90d') return { start: formatDateInput(shift(89)), end: formatDateInput(end) }
      if (preset === 'mtd') {
        return {
          start: formatDateInput(new Date(end.getFullYear(), end.getMonth(), 1)),
          end: formatDateInput(end),
        }
      }
      if (preset === 'ytd') {
        return {
          start: formatDateInput(new Date(end.getFullYear(), 0, 1)),
          end: formatDateInput(end),
        }
      }
      return { start: '', end: '' }
    }

    /** The preset shown in the toolbar follows the actual dates, so manual dates read "Custom". */
    const periodPreset = computed({
      get() {
        if (!startDate.value && !endDate.value) return ''
        for (const option of periodOptions) {
          if (!option.value || option.value === 'custom') continue
          const range = rangeForPreset(option.value)
          if (range.start === startDate.value && range.end === endDate.value) return option.value
        }
        return 'custom'
      },
      set(value) {
        if (value === 'custom') {
          filtersOpen.value = true
          return
        }
        const range = rangeForPreset(value)
        startDate.value = range.start
        endDate.value = range.end
      },
    })

    const filters = computed(() => {
      const f = {}
      if (startDate.value) f.start_date = startDate.value
      if (endDate.value) f.end_date = endDate.value
      if (accountFilter.value) f.account_ids = [accountFilter.value]
      if (txType.value) f.tx_type = txType.value
      if (sortOption.value && sortOption.value !== 'date_desc') f.sort = sortOption.value
      return { ...f, ...tableFilters.value }
    })

    const {
      searchQuery,
      currentPage,
      totalPages,
      totalCount,
      currentPageRows,
      queryFilters,
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

    // A server-side order is authoritative: switch the loaded-page client sort off so it cannot
    // reshuffle rows by date. Back to "Newest" restores the default client sort.
    watch(sortOption, (value) => {
      if (value === 'date_desc') {
        sortKey.value = 'date'
        sortOrder.value = -1
      } else {
        sortKey.value = null
      }
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
    const tabs = ['Activity', 'Recurring', { label: 'Transfer Review', slot: 'Scanner' }]
    const activeTab = ref(
      coerceQueryValue(route.query?.tab) === 'Recurring' ? 'Recurring' : 'Activity',
    )

    /**
     * Determine whether a top-level transaction filter is currently active.
     *
     * @returns {boolean}
     */
    const hasActiveFilters = computed(() =>
      Boolean(startDate.value || endDate.value || accountFilter.value || txType.value),
    )

    /** Rows of the current server page, exactly what the table renders. */
    const pageRows = computed(() =>
      Array.isArray(currentPageRows.value) ? currentPageRows.value : [],
    )

    const matchingTotal = computed(() => Number(totalCount.value || 0))

    /** Count label that never presents a page as the whole matching set. */
    const resultCountLabel = computed(() => {
      const matching = matchingTotal.value.toLocaleString('en-US')
      return `${pageRows.value.length} on this page · ${matching} matching`
    })

    const matchingCountLabel = computed(() => {
      const count = matchingTotal.value
      return `${count.toLocaleString('en-US')} ${count === 1 ? 'match' : 'matches'}`
    })

    /** Subtotal of the rows actually rendered on this page (not the filtered dataset total). */
    const pageSubtotal = computed(() => visiblePageSubtotal(pageRows.value))

    // All-matching totals from the server for the identical filter set the table and export use.
    const summaryFilters = computed(() => queryFilters?.value ?? filters.value)
    const hasAnyFilter = computed(() =>
      Boolean(
        startDate.value ||
        endDate.value ||
        accountFilter.value ||
        txType.value ||
        String(searchQuery.value || '').trim() ||
        Object.keys(tableFilters.value).length,
      ),
    )
    const {
      matchingSummary,
      status: summaryStatus,
      stale: summaryStale,
      refresh: refreshSummary,
    } = useTransactionSummary(summaryFilters, hasAnyFilter)

    const movementRows = computed(() => {
      const data = matchingSummary.value
      if (!data) return []
      const rows = []
      const add = (label, value) => {
        if (Number(value)) rows.push({ label, value: formatCurrency(value) })
      }
      add('Transfers in', data.transfers_in)
      add('Transfers out', data.transfers_out)
      add('Debt payments', data.debt_settlements)
      add('Investment movement', data.investment_movements)
      add('Unreviewed inflows', data.unclassified_in)
      add('Unreviewed outflows', data.unclassified_out)
      if (data.needs_review_count)
        rows.push({ label: 'Needs review', value: `${data.needs_review_count} rows` })
      if (data.pending_excluded_count) {
        rows.push({ label: 'Pending, not counted', value: `${data.pending_excluded_count} rows` })
      }
      return rows
    })

    /** A table edit or transfer decision can change classification: refresh page and totals. */
    function onTransactionsChanged() {
      refreshSummary()
    }

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

    /** Chips for every filter in play, including search and the table's column filters. */
    const scopeChips = computed(() => {
      const chips = [...activeFilterChips.value]
      const term = String(searchQuery.value || '').trim()
      if (term) chips.push(`Search: ${term}`)
      for (const [key, value] of Object.entries(tableFilters.value)) {
        const label = key
          .replace(/^filter_/, '')
          .replace(/^category_primary$/, 'category')
          .replace(/^category_sub$/, 'subcategory')
          .replace(/_/g, ' ')
        chips.push(`${label}: ${value}`)
      }
      return chips
    })

    // --- Insights: server-side summaries and review queue over ALL matching rows --------------------
    const insights = ref(null)
    const insightsLoading = ref(false)
    const insightsError = ref('')
    let insightsTimer = null

    /** Plain-language scope for the summary, so it is never mistaken for the table's range. */
    const insightsScopeLabel = computed(() => {
      const range =
        startDate.value || endDate.value
          ? `${startDate.value || '…'} – ${endDate.value || 'today'}`
          : 'Last 30 days (pick a period to change)'
      return accountFilter.value ? `${range} · selected account` : range
    })

    async function loadInsights(refresh = false) {
      insightsLoading.value = true
      insightsError.value = ''
      try {
        const res = await api.getTransactionInsights({
          start_date: startDate.value || undefined,
          end_date: endDate.value || undefined,
          account_ids: accountFilter.value ? [accountFilter.value] : undefined,
          refresh: refresh ? true : undefined,
        })
        insights.value = res?.data ?? null
      } catch (err) {
        console.error('Failed to load transaction insights', err)
        const data = err?.response?.data
        insightsError.value =
          data?.code === 'owner_not_configured'
            ? 'The summary is not set up on this server yet (PYNANCE_OWNER_USER_ID is missing).'
            : data?.message || 'Unable to load the summary.'
      } finally {
        insightsLoading.value = false
      }
    }

    watch([startDate, endDate, accountFilter], () => {
      clearTimeout(insightsTimer)
      insightsTimer = setTimeout(() => loadInsights(), 300)
    })

    /**
     * Apply a review-queue item: open Transfer Review, or narrow the explorer to the evidence.
     * Never edits a transaction.
     *
     * @param {{kind: string, filter?: Record<string, unknown>, transaction_ids?: string[]}} item
     */
    function applyReviewItem(item) {
      if (item.kind === 'transfer_candidate') {
        activeTab.value = 'Scanner'
        return
      }
      const filter = item.filter || {}
      if (filter.start_date || filter.end_date) {
        startDate.value = String(filter.start_date || '')
        endDate.value = String(filter.end_date || '')
      }
      if (filter.search) searchQuery.value = String(filter.search)
      else if (filter.uncategorized) searchQuery.value = 'Uncategorized'
      else if (filter.category_contains) searchQuery.value = String(filter.category_contains)
      else searchQuery.value = item.transaction_ids?.[0] || ''
      nextTick(() =>
        document.getElementById('activity-toolbar')?.scrollIntoView?.({ block: 'start' }),
      )
    }

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
      if (Object.keys(tableFilters.value).length) {
        tableFilters.value = {}
        tableResetKey.value += 1 // remount the table so its own filter inputs reset too
      }
    }

    /**
     * Open the Recurring tab and pre-fill its form from a transaction row through the child's
     * explicit `openFromTransaction` API. If the tab has not mounted yet, the call is made as soon
     * as the child ref appears.
     *
     * @param {Record<string, unknown>} tx
     */
    async function prefillRecurringFromTransaction(tx) {
      activeTab.value = 'Recurring'
      await nextTick()
      if (recurringFormRef.value?.openFromTransaction) {
        recurringFormRef.value.openFromTransaction(tx)
        return
      }
      const stop = watch(recurringFormRef, (child) => {
        if (child?.openFromTransaction) {
          child.openFromTransaction(tx)
          stop()
        }
      })
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
        // The same canonical filters as the table page and the totals, including search and
        // column filters, so the file contains exactly the rows being counted.
        const activeFilters = {
          ...(summaryFilters.value || {}),
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

        const rowsForExport = allRows

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
      loadInsights()
    })

    return {
      tabs,
      activeTab,
      searchQuery,
      currentPage,
      totalPages,
      totalCount,
      initialPageSize,
      pageRows,
      pageSubtotal,
      matchingCountLabel,
      matchingSummary,
      summaryStatus,
      summaryStale,
      refreshSummary,
      movementRows,
      scopeChips,
      hasAnyFilter,
      tableFilters,
      tableResetKey,
      onTransactionsChanged,
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
      formatCurrency,
      sortOptions,
      sortOption,
      periodOptions,
      periodPreset,
      resultCountLabel,
      insights,
      insightsLoading,
      insightsError,
      insightsScopeLabel,
      loadInsights,
      applyReviewItem,
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

/* Compact selects share one row with the search box instead of each taking a full line. */
.activity-toolbar__row :deep(select) {
  width: auto;
  min-width: 9rem;
  max-width: 16rem;
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

.filter-summary__scope,
.filter-summary__page {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.25rem 0.75rem;
  flex-basis: 100%;
}

.filter-summary__heading {
  font-weight: 700;
}

.filter-summary__page,
.filter-summary__note,
.filter-summary__movement {
  color: var(--color-text-muted);
}

.filter-summary__retry {
  text-decoration: underline;
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
  overflow-wrap: anywhere;
  min-width: 0;
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: var(--color-text-light);
}
</style>
