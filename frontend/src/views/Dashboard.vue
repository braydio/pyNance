<!--
  Dashboard.vue
  Main application dashboard showing snapshots, charts, and financial summaries.
-->
<template>
  <!-- Page title for accessibility (screen-reader only) -->
  <h1 class="sr-only">Dashboard - Financial Overview</h1>
  <BasePageLayout gap="gap-8">
    <!-- NET OVERVIEW -->
    <Suspense>
      <template #default>
        <NetOverviewSection
          :user-name="userName"
          :current-date="currentDate"
          :net-worth-message="netWorthMessage"
          :date-range="dateRange"
          :debounced-range="debouncedRange"
          :net-range="netRange"
          :net-timeframe="netTimeframe"
          :zoomed-out="zoomedOut"
          :net-summary="netSummary"
          :chart-data="chartData"
          :show7-day="show7Day"
          :show30-day="show30Day"
          :show-avg-income="showAvgIncome"
          :show-avg-expenses="showAvgExpenses"
          :show-comparison-overlay="showComparisonOverlay"
          :comparison-mode="comparisonMode"
          @update:start-date="dateRange.start = $event"
          @update:end-date="dateRange.end = $event"
          @update:zoomed-out="zoomedOut = $event"
          @update:show7-day="show7Day = $event"
          @update:show30-day="show30Day = $event"
          @update:show-avg-income="showAvgIncome = $event"
          @update:show-avg-expenses="showAvgExpenses = $event"
          @update:show-comparison-overlay="showComparisonOverlay = $event"
          @update:comparison-mode="comparisonMode = $event"
          @update:net-timeframe="netTimeframe = $event"
          @net-summary-change="netSummary = $event"
          @net-data-change="chartData = $event"
          @net-bar-click="onNetBarClick"
        />
      </template>

      <template #fallback>
        <section
          data-testid="net-overview-skeleton"
          class="flex flex-col gap-4 bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-cyan)] p-6 animate-pulse"
          aria-busy="true"
        >
          <div class="h-6 w-1/3 bg-[var(--divider)] rounded mb-2" />
          <div class="h-4 w-1/4 bg-[var(--divider)] rounded mb-2" />
          <div class="h-4 w-1/2 bg-[var(--divider)] rounded mb-4" />
          <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
            <SkeletonCard />
            <div class="md:col-span-2">
              <SkeletonCard />
            </div>
          </div>
        </section>
      </template>
    </Suspense>

    <!-- CATEGORY BREAKDOWN -->
    <InsightsRow>
      <Suspense>
        <template #default>
          <CategoryBreakdownSection
            :start-date="debouncedRange.start"
            :end-date="debouncedRange.end"
            :category-groups="categoryGroups"
            :selected-category-ids="selectedCategoryIds"
            :group-others="groupOthers"
            :breakdown-type="breakdownType"
            :summary="catSummary"
            @change-breakdown="setDashboardBreakdownMode"
            @toggle-group-others="toggleGroupOthers"
            @update-selection="updateSelection"
            @categories-change="onCategoriesChange"
            @summary-change="catSummary = $event"
            @bar-click="onCategoryBarClick"
          />
        </template>

        <template #fallback>
          <section
            data-testid="breakdown-skeleton"
            class="bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-cyan)] p-6 animate-pulse"
          >
            <div class="h-6 w-40 bg-[var(--divider)] rounded mb-4" />
            <div class="grid grid-cols-2 gap-3">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          </section>
        </template>
      </Suspense>
    </InsightsRow>

    <!-- REVIEW TRANSACTIONS CARD -->
    <div class="review-cta-card dashboard-panel p-6 md:p-7">
      <div class="dashboard-panel-header gap-6">
        <div class="space-y-3">
          <div class="dashboard-panel-kicker">Review Workflow</div>
          <div class="flex flex-wrap items-center gap-3">
            <h2 class="dashboard-panel-title">Review Transactions</h2>
            <span class="dashboard-status-pill">
              <span class="dashboard-status-dot" />
              {{ reviewCountLabel }}
            </span>
          </div>
          <p class="dashboard-panel-copy">
            Step through transactions in batches of 10, approve quickly, or edit in place without
            leaving the dashboard.
          </p>
        </div>
        <div class="review-cta-meta">
          <span class="review-cta-meta-label">Workflow</span>
          <span class="review-cta-meta-value">Batch / inline edits / tag filter</span>
        </div>
      </div>
      <div class="review-cta-grid">
        <div class="mt-1 flex flex-col gap-2 max-w-sm">
          <label class="text-xs uppercase tracking-[0.2em] text-[var(--color-text-muted)]">
            Tag filter
          </label>
          <input
            v-model="reviewTagFilter"
            class="input review-filter-input"
            type="text"
            placeholder="Optional tag (e.g., #groceries)"
          />
        </div>
        <div class="review-cta-action-wrap">
          <button class="btn btn-outline review-start-btn" @click="openReviewModal">
            Start Review
          </button>
        </div>
      </div>
    </div>

    <!-- RESERVED TABLES PANEL -->
    <div
      data-testid="tables-panel"
      class="dashboard-panel tables-panel-shell relative min-h-[55vh] sm:min-h-[60vh] lg:min-h-[65vh] overflow-hidden"
    >
      <transition name="accordion">
        <div
          v-if="!accountsExpanded && !transactionsExpanded"
          data-testid="tables-panel-cta"
          class="flex h-full w-full flex-col justify-center gap-8 p-6 sm:p-10 lg:p-12"
        >
          <div class="dashboard-panel-header gap-4">
            <div class="space-y-2">
              <div class="dashboard-panel-kicker">Drill Down</div>
              <h2 class="dashboard-panel-title">Choose a lower dashboard surface</h2>
              <p class="dashboard-panel-copy mb-0">
                Open either the account ledger or the transaction queue from the same panel shell.
              </p>
            </div>
          </div>
          <div class="tables-panel-grid">
            <button
              class="tables-panel-option tables-panel-option--accounts"
              @click="expandAccounts"
            >
              <div class="tables-panel-option-header">
                <Wallet class="w-7 h-7" />
                <span>Accounts</span>
              </div>
              <p>Balances, linked institutions, and account-level drill downs.</p>
            </button>
            <button
              class="tables-panel-option tables-panel-option--transactions"
              @click="expandTransactions"
            >
              <div class="tables-panel-option-header">
                <CreditCard class="w-7 h-7" />
                <span>Transactions</span>
              </div>
              <p>Searchable activity history, pagination, and review handoff.</p>
            </button>
          </div>
        </div>
      </transition>
      <transition name="modal-fade-slide">
        <Suspense v-if="accountsExpanded">
          <template #default>
            <AccountsSection @close="collapseTables" />
          </template>
          <template #fallback>
            <section
              data-testid="accounts-skeleton"
              class="absolute inset-0 p-6 sm:p-8 bg-[var(--color-bg-sec)] animate-pulse"
              aria-busy="true"
            >
              <div class="h-6 w-48 bg-[var(--divider)] rounded mb-4" />
              <div class="h-[55vh] bg-[var(--divider)] rounded" />
            </section>
          </template>
        </Suspense>
      </transition>
      <transition name="modal-fade-slide">
        <Suspense v-if="transactionsExpanded">
          <template #default>
            <TransactionsSection
              :transactions="filteredTransactions"
              :sort-key="sortKey"
              :sort-order="sortOrder"
              :search="searchQuery"
              :current-page="currentPage"
              :total-pages="totalPages"
              :page-size="pageSize"
              :total-count="totalCount"
              @sort="setSort"
              @change-page="changePage"
              @set-page="setPage"
              @close="collapseTables"
            />
          </template>
          <template #fallback>
            <section
              data-testid="transactions-skeleton"
              class="absolute inset-0 p-6 sm:p-8 bg-[var(--color-bg-sec)] animate-pulse"
              aria-busy="true"
            >
              <div class="h-6 w-56 bg-[var(--divider)] rounded mb-4" />
              <div class="h-[55vh] bg-[var(--divider)] rounded" />
            </section>
          </template>
        </Suspense>
      </transition>
    </div>

    <TransactionModal
      :show="showDailyModal"
      kind="date"
      :show-date-column="false"
      :hide-category-visuals="false"
      :subtitle="dailyModalSubtitle"
      :transactions="dailyModalTransactions"
      @close="closeModal('daily')"
    />
    <TransactionModal
      :show="showCategoryModal"
      kind="category"
      :show-date-column="true"
      :hide-category-visuals="false"
      :subtitle="categoryModalSubtitle"
      :subtitle-prefix="categoryModalSubtitlePrefix"
      :transactions="categoryModalTransactions"
      @close="closeModal('category')"
    />
    <TransactionReviewModal
      v-if="showReviewModal"
      :show="showReviewModal"
      :filters="reviewFilters"
      @close="closeReviewModal"
    />
  </BasePageLayout>
</template>

<script setup>
/**
 * Dashboard view showing financial summaries, charts, and drill-down modals.
 */
import { ref, computed, onMounted, defineAsyncComponent, watch } from 'vue'
import { Wallet, CreditCard } from 'lucide-vue-next'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import TransactionModal from '@/components/modals/TransactionModal.vue'
import TransactionReviewModal from '@/components/transactions/TransactionReviewModal.vue'
import SkeletonCard from '@/components/ui/SkeletonCard.vue'
import api from '@/services/api'
import { useTransactions } from '@/composables/useTransactions.js'
import { formatDateInput, useDateRange } from '@/composables/useDateRange'
import { fetchTransactions as fetchTransactionsApi } from '@/api/transactions'
import { useCategories } from '@/composables/useCategories'
import { useDashboardModals } from '@/composables/useDashboardModals'

const DASHBOARD_ACCOUNT_SYNC_STORAGE_KEY = 'dashboard:last-account-sync-at'
const DASHBOARD_ACCOUNT_SYNC_INTERVAL_MS = 30 * 60 * 1000

/* Async components */
const NetOverviewSection = defineAsyncComponent(
  () => import('@/components/dashboard/NetOverviewSection.vue'),
)
const CategoryBreakdownSection = defineAsyncComponent(
  () => import('@/components/dashboard/CategoryBreakdownSection.vue'),
)
const InsightsRow = defineAsyncComponent(() => import('@/components/dashboard/InsightsRow.vue'))
const AccountsSection = defineAsyncComponent(
  () => import('@/components/dashboard/AccountsSection.vue'),
)
const TransactionsSection = defineAsyncComponent(
  () => import('@/components/dashboard/TransactionsSection.vue'),
)

// Transactions and user
const pageSize = 15
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
  changePage,
  fetchTransactions: loadTransactions,
} = useTransactions(pageSize)
// Modal manager
const { openModal, closeModal, isVisible } = useDashboardModals()
const showDailyModal = isVisible('daily')
const dailyModalTransactions = ref([])
const dailyModalSubtitle = ref('')
const showReviewModal = isVisible('review')

// Category modal state
const showCategoryModal = isVisible('category')
const categoryModalTransactions = ref([])
const categoryModalSubtitle = ref('')
const categoryModalSubtitlePrefix = ref('')
const plaidUserId = import.meta.env.VITE_USER_ID_PLAID || ''
const userName = plaidUserId || 'Guest'
const currentDate = new Date().toLocaleDateString(undefined, {
  month: 'long',
  day: 'numeric',
  year: 'numeric',
})
const netWorth = ref(0)
const loadErrorMessage = ref('')
const netWorthMessage = computed(() => {
  if (loadErrorMessage.value) {
    return loadErrorMessage.value
  }
  if (netWorth.value < 0) return '... and things are looking quite bleak.'
  if (netWorth.value > 1000) return 'Ahh... well in the black.'
  return 'Uhh... keep up the... whatever this is.'
})

/** --- DAILY NET STATE --- */
const netSummary = ref({
  totalIncome: 0,
  totalExpenses: 0,
  totalNet: 0,
})
const chartData = ref([])
const zoomedOut = ref(false)
const show7Day = ref(false)
const show30Day = ref(false)
const showAvgIncome = ref(false)
const showAvgExpenses = ref(false)
const showComparisonOverlay = ref(false)
const comparisonMode = ref('prior_month_to_date')
const netTimeframe = ref('mtd')
let activeLoadToken = 0

const netRange = computed(() => {
  const today = new Date()
  const end = formatDateInput(today)

  if (netTimeframe.value === 'rolling_30') {
    const startDate = new Date(today)
    startDate.setDate(startDate.getDate() - 29)
    return {
      start: formatDateInput(startDate),
      end,
    }
  }

  const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
  return {
    start: formatDateInput(monthStart),
    end,
  }
})

const catSummary = ref({ total: 0, startDate: '', endDate: '' })
const {
  breakdownType,
  groupOthers,
  selectedIds: selectedCategoryIds,
  groupedOptions: categoryGroups,
  toggleGroupOthers,
  setAvailableIds,
  updateSelection,
  resetSelection,
  setBreakdownType,
  refreshOptions,
  loadMerchantGroups,
} = useCategories()

// --- SHARED DATE RANGE STATE ---
/**
 * Reset spending selections when the date range changes and trigger a full
 * dashboard refresh with the new boundaries.
 *
 * @param {{ start: string; end: string }} range - Debounced date range boundaries.
 */
async function onDateRangeChange(range) {
  resetSelection()
  await loadDashboardData(range)
}

const { dateRange = ref({ start: '', end: '' }), debouncedRange = ref({ start: '', end: '' }) } =
  useDateRange({
    onDebouncedChange: onDateRangeChange,
  })

const reviewTagFilter = ref('')
const normalizedReviewTag = computed(() => reviewTagFilter.value.trim())
const reviewCount = ref(0)
const reviewCountLoading = ref(false)
const reviewCountError = ref(false)
let reviewCountToken = 0

const reviewFilters = computed(() => {
  const filters = {
    start_date: debouncedRange.value.start,
    end_date: debouncedRange.value.end,
  }
  if (normalizedReviewTag.value) {
    filters.tags = normalizedReviewTag.value
  }
  return filters
})

const reviewCountLabel = computed(() => {
  if (reviewCountLoading.value) return 'Loading…'
  if (reviewCountError.value) return 'Count unavailable'
  return `${reviewCount.value} to review`
})

async function loadReviewCount(filters = reviewFilters.value) {
  const token = ++reviewCountToken
  reviewCountLoading.value = true
  reviewCountError.value = false

  try {
    const result = await fetchTransactionsApi({
      page: 1,
      page_size: 1,
      ...filters,
    })
    if (token !== reviewCountToken) return
    const total = Number(result.total ?? result.total_count ?? result.count ?? 0)
    reviewCount.value = Number.isFinite(total) ? total : 0
  } catch (error) {
    if (token !== reviewCountToken) return
    console.error('Failed to load review count', error)
    reviewCountError.value = true
    reviewCount.value = 0
  } finally {
    if (token === reviewCountToken) {
      reviewCountLoading.value = false
    }
  }
}

/**
 * Perform the dashboard's initial data load in parallel so hero, breakdown,
 * and transaction widgets all start with fresh data. Applies a shared fallback
 * message when any fetch fails so the UI surfaces a consistent error tone. The
 * optional range argument enables debounced refreshes without overlapping the
 * results from earlier requests.
 *
 * @param {{ start: string; end: string }} [range] - Date boundaries to apply to
 *   option and transaction requests.
 * @returns {Promise<void>} Resolves when the dashboard data requests settle.
 */
async function loadDashboardData(range = debouncedRange.value) {
  const loadToken = ++activeLoadToken
  const params = {
    start_date: range.start,
    end_date: range.end,
  }
  const fallback = 'Unable to refresh dashboard data. Showing the latest available info.'
  loadErrorMessage.value = ''

  const recordFailure = (error) => {
    console.error('Failed to load dashboard data:', error)
    return { __error: error }
  }

  try {
    const [netAssetsResult, categoriesResult, transactionsResult] = await Promise.all([
      api.fetchNetAssets().catch(recordFailure),
      refreshOptions(params).catch(recordFailure),
      loadTransactions(1, { force: true }).catch(recordFailure),
    ])
    loadReviewCount(reviewFilters.value)

    if (loadToken !== activeLoadToken) {
      return
    }

    const hadFailure =
      [categoriesResult, transactionsResult].some((result) => result && '__error' in result) ||
      (netAssetsResult && '__error' in netAssetsResult)

    if (netAssetsResult?.status === 'success' && Array.isArray(netAssetsResult.data)) {
      const lastPoint = netAssetsResult.data[netAssetsResult.data.length - 1]
      netWorth.value = lastPoint?.net_assets ?? 0
    } else {
      loadErrorMessage.value = fallback
    }

    if (hadFailure) {
      loadErrorMessage.value = fallback
    }
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    loadErrorMessage.value = fallback
  }
}

const accountsExpanded = isVisible('accounts')
const transactionsExpanded = isVisible('transactions')
function expandAccounts() {
  openModal('accounts')
}
function expandTransactions() {
  openModal('transactions')
}
function collapseTables() {
  closeModal()
}

/**
 * Open the transaction review modal with mutual exclusivity.
 */
function openReviewModal() {
  openModal('review')
}

/**
 * Close the transaction review modal and clear visibility state.
 */
function closeReviewModal() {
  closeModal('review')
}

/**
 * Convert chart labels into ISO date strings accepted by the transactions API
 * without shifting the date across timezones. Falls back to the original label
 * when parsing fails so the modal still opens, even if no data is returned.
 *
 * @param {string} label - Label emitted from the DailyNetChart click handler.
 * @returns {string} ISO-formatted date (YYYY-MM-DD) when parseable, otherwise
 *   the original label value.
 */
function normalizeDateLabel(label) {
  const rawLabel = String(label ?? '').trim()
  if (!rawLabel) return label

  // Fast path for ISO-like strings (YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss)
  const isoMatch = rawLabel.match(/^(\d{4}-\d{2}-\d{2})/)
  if (isoMatch) return isoMatch[1]

  const parsed = new Date(rawLabel)
  if (Number.isNaN(parsed.getTime())) return label

  const year = parsed.getFullYear()
  const month = String(parsed.getMonth() + 1).padStart(2, '0')
  const day = String(parsed.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

async function onNetBarClick(label) {
  // Fetch *all* transactions for the clicked date so the modal matches the
  // counts and amounts shown in the DailyNetChart. Use a large page_size to
  // avoid pagination truncation for high-activity days.
  const isoDate = normalizeDateLabel(label)

  try {
    const result = await fetchTransactionsApi({
      start_date: isoDate,
      end_date: isoDate,
      page: 1,
      page_size: 1000,
    })
    dailyModalTransactions.value = result.transactions || []
  } catch (error) {
    console.error('Failed to fetch transactions for date', label, error)
    dailyModalTransactions.value = []
  }

  dailyModalSubtitle.value = isoDate
  openModal('daily')
}

/**
 * Handle clicks on the category breakdown chart.
 *
 * Fetches transactions for the clicked category (or merchant) within the active
 * date range and displays them in a modal dialog. If the clicked bar
 * does not correspond to any user-selected categories, no modal is shown.
 *
 * @param {object|string} payload - Click payload from the chart containing
 *   the bar label and an array of category IDs.
 */
async function onCategoryBarClick(payload) {
  const { label, ids = [] } = typeof payload === 'object' ? payload : { label: payload, ids: [] }

  // If merchant mode, handle with dedicated merchant handler
  if (breakdownType.value === 'merchant') {
    await onMerchantBarClick({ label, merchantId: ids[0] })
    return
  }

  // Only display the modal when the clicked bar corresponds to selected categories
  if (!ids.length) return

  // Determine the date range in effect for the category chart. The chart emits
  // `summary-change` events that populate `catSummary` with the actual start
  // and end dates used in its query. This ensures the modal reflects the same
  // range, even if it differs from the user-selected inputs.
  const start = catSummary.value.startDate || debouncedRange.value.start
  const end = catSummary.value.endDate || debouncedRange.value.end

  const result = await fetchTransactionsApi({
    category_ids: ids,
    start_date: start,
    end_date: end,
  })
  categoryModalTransactions.value = result.transactions || []
  categoryModalSubtitle.value = label // Focus on category label in header; dates live in table.
  categoryModalSubtitlePrefix.value = 'Category'
  openModal('category')
}

/**
 * Handle clicks on merchant bars in the breakdown chart.
 *
 * Fetches all transactions for the selected merchant within the active
 * date range and displays them in a modal.
 *
 * @param {object} payload - Click payload containing merchant label and ID.
 */
async function onMerchantBarClick({ label, merchantId }) {
  if (!merchantId) return

  const start = catSummary.value.startDate || debouncedRange.value.start
  const end = catSummary.value.endDate || debouncedRange.value.end

  const result = await fetchTransactionsApi({
    merchant: merchantId,
    start_date: start,
    end_date: end,
  })

  categoryModalTransactions.value = result.transactions || []
  categoryModalSubtitle.value = label
  categoryModalSubtitlePrefix.value = 'Merchant'
  openModal('category')
}

/**
 * Track IDs emitted from the category chart and refresh dropdown defaults.
 *
 * @param {Array} ids - Category or merchant identifiers emitted from the chart.
 */
function onCategoriesChange(ids) {
  setAvailableIds(ids)
}

/**
 * Switch spending breakdown modes and ensure merchant dropdown options stay current.
 *
 * @param {string} mode - Breakdown dimension to display.
 */
async function setDashboardBreakdownMode(mode) {
  setBreakdownType(mode)
  if (mode === 'merchant') {
    await loadMerchantGroups({
      start_date: debouncedRange.value.start,
      end_date: debouncedRange.value.end,
    })
  }
}

function getStoredDashboardAccountSyncAt() {
  if (typeof localStorage === 'undefined') return 0

  try {
    return Number(localStorage.getItem(DASHBOARD_ACCOUNT_SYNC_STORAGE_KEY) || 0)
  } catch {
    return 0
  }
}

function setStoredDashboardAccountSyncAt(timestamp = Date.now()) {
  if (typeof localStorage === 'undefined') return

  try {
    localStorage.setItem(DASHBOARD_ACCOUNT_SYNC_STORAGE_KEY, String(timestamp))
  } catch {
    // Ignore storage errors and keep the dashboard usable.
  }
}

async function maybeAutoSyncAccounts() {
  if (!plaidUserId) return

  const lastSyncAt = getStoredDashboardAccountSyncAt()
  if (Date.now() - lastSyncAt < DASHBOARD_ACCOUNT_SYNC_INTERVAL_MS) {
    return
  }

  setStoredDashboardAccountSyncAt()

  try {
    await api.refreshAccounts({ user_id: plaidUserId })
    await loadDashboardData()
  } catch (error) {
    console.error('Failed to auto-sync dashboard accounts:', error)
  }
}

onMounted(() => {
  loadDashboardData()
  maybeAutoSyncAccounts()
})
watch(reviewFilters, (filters) => loadReviewCount(filters), { immediate: true })

/**
 * The modal manager in `useDashboardModals` keeps overlays mutually exclusive so
 * chart interactions cannot stack dialogs or expanded panels.
 */
</script>

<style scoped>
.review-cta-card {
  background: linear-gradient(
    150deg,
    color-mix(in srgb, var(--color-accent-purple) 18%, var(--color-bg-sec)) 0%,
    color-mix(in srgb, var(--color-accent-cyan) 10%, var(--color-bg-sec)) 100%
  );
}

.review-cta-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 1rem;
  align-items: end;
  margin-top: 1.25rem;
}

.review-cta-meta {
  display: inline-flex;
  flex-direction: column;
  gap: 0.3rem;
  min-width: 15rem;
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  border: 1px solid color-mix(in srgb, var(--color-accent-cyan) 28%, var(--divider));
  background: color-mix(in srgb, var(--color-bg-dark) 76%, transparent);
}

.review-cta-meta-label {
  font-family: var(--font-display);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-accent-cyan);
}

.review-cta-meta-value {
  color: color-mix(in srgb, var(--color-text-light) 78%, var(--color-text-muted));
  font-size: 0.85rem;
}

.review-cta-action-wrap {
  display: flex;
  align-items: end;
  justify-content: flex-start;
}

.review-filter-input {
  min-height: 2.4rem;
  border-color: color-mix(in srgb, var(--color-accent-purple) 38%, var(--divider));
  background: color-mix(in srgb, var(--color-bg-dark) 88%, transparent);
}

.review-filter-input:focus {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-accent-purple) 55%, transparent);
}

.review-start-btn {
  min-width: 9.75rem;
  min-height: 3rem;
  justify-content: center;
  border-radius: 1rem;
  border-color: color-mix(in srgb, var(--color-accent-cyan) 55%, var(--color-accent-purple));
  color: var(--color-accent-cyan);
}

.review-start-btn:hover {
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--color-accent-cyan) 78%, var(--color-accent-purple)) 0%,
    var(--color-accent-purple) 100%
  );
  color: var(--color-bg-dark);
}

.tables-panel-shell {
  min-height: 55vh;
}

.tables-panel-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 1rem;
}

.tables-panel-option {
  display: flex;
  min-height: 13rem;
  flex-direction: column;
  justify-content: space-between;
  gap: 1rem;
  border-radius: 1.25rem;
  border: 1px solid var(--divider);
  padding: 1.5rem;
  text-align: left;
  transition:
    transform 0.22s ease,
    border-color 0.22s ease,
    box-shadow 0.22s ease,
    background-color 0.22s ease;
}

.tables-panel-option:hover {
  transform: translateY(-2px);
}

.tables-panel-option p {
  margin: 0;
  color: color-mix(in srgb, var(--color-text-light) 76%, var(--color-text-muted));
  font-size: 0.9rem;
  line-height: 1.65;
}

.tables-panel-option-header {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.tables-panel-option--accounts {
  background: linear-gradient(
    145deg,
    color-mix(in srgb, var(--color-accent-cyan) 18%, var(--color-bg-dark)) 0%,
    color-mix(in srgb, var(--color-bg-sec) 88%, transparent) 100%
  );
  border-color: color-mix(in srgb, var(--color-accent-cyan) 55%, var(--divider));
  color: var(--color-accent-cyan);
}

.tables-panel-option--accounts:hover {
  box-shadow: 0 16px 32px rgba(14, 31, 44, 0.44);
}

.tables-panel-option--transactions {
  background: linear-gradient(
    145deg,
    color-mix(in srgb, var(--color-accent-red) 16%, var(--color-bg-dark)) 0%,
    color-mix(in srgb, var(--color-bg-sec) 88%, transparent) 100%
  );
  border-color: color-mix(in srgb, var(--color-accent-red) 52%, var(--divider));
  color: var(--color-accent-red);
}

.tables-panel-option--transactions:hover {
  box-shadow: 0 16px 32px rgba(44, 14, 20, 0.42);
}

@media (min-width: 768px) {
  .review-cta-grid {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .review-cta-action-wrap {
    justify-content: flex-end;
  }

  .tables-panel-shell {
    min-height: 60vh;
  }

  .tables-panel-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .tables-panel-shell {
    min-height: 65vh;
  }
}
</style>
