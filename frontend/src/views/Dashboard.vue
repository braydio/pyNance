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
          :current-date="currentDate"
          :activity-status-message="activityStatusMessage"
          :load-error-message="loadErrorMessage"
          :reconnect-count="reconnectCount"
          :date-range="dateRange"
          :debounced-range="debouncedRange"
          :net-timeframe="selectedPreset"
          :zoomed-out="zoomedOut"
          :net-summary="netSummary"
          :chart-data="chartData"
          :show7-day="show7Day"
          :show30-day="show30Day"
          :show-avg-income="showAvgIncome"
          :show-avg-expenses="showAvgExpenses"
          :show-comparison-overlay="showComparisonOverlay"
          :comparison-mode="comparisonMode"
          :safe-to-spend="safeToSpend"
          :safe-to-spend-loading="safeToSpendLoading"
          :safe-to-spend-error="safeToSpendError"
          :safe-to-spend-mode="safeToSpendMode"
          :period-transaction-count="periodTransactionCount"
          :period-transaction-count-loading="periodTransactionCountLoading"
          :period-transaction-count-error="periodTransactionCountError"
          :review-tag-filter="reviewTagFilter"
          @update:review-tag-filter="reviewTagFilter = $event"
          @update:start-date="setManualStartDate"
          @update:end-date="setManualEndDate"
          @update:zoomed-out="zoomedOut = $event"
          @update:show7-day="show7Day = $event"
          @update:show30-day="show30Day = $event"
          @update:show-avg-income="showAvgIncome = $event"
          @update:show-avg-expenses="showAvgExpenses = $event"
          @update:show-comparison-overlay="showComparisonOverlay = $event"
          @update:comparison-mode="comparisonMode = $event"
          @update:net-timeframe="setDashboardPeriodPreset"
          @update:safe-to-spend-mode="setSafeToSpendMode"
          @net-summary-change="netSummary = $event"
          @net-data-change="chartData = $event"
          @net-bar-click="onNetBarClick"
          @select-date="onNetBarClick"
          @open-review="openReviewModal"
        />
      </template>

      <template #fallback>
        <section
          data-testid="net-overview-skeleton"
          class="dashboard-skeleton-panel flex flex-col gap-4 bg-[var(--color-bg-sec)] ui-radius-2 border-2 border-[var(--edge-contrast-accent-cyan)] p-6 animate-pulse"
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
            class="dashboard-skeleton-panel bg-[var(--color-bg-sec)] ui-radius-2 border-2 border-[var(--edge-contrast-accent-cyan)] p-6 animate-pulse"
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

    <!-- TIER 3: ACCOUNT SNAPSHOT -->
    <div class="surface-normal p-4 md:p-5" data-testid="account-snapshot">
      <TopAccountSnapshot />
    </div>

    <!-- TIER 4: DRILL DOWN -->
    <nav class="explore-details" aria-label="Explore details" data-testid="explore-details">
      <span class="explore-details__label">Explore details</span>
      <router-link to="/accounts" class="btn btn-outline explore-details__link">
        <Wallet class="w-4 h-4" aria-hidden="true" /> Accounts
      </router-link>
      <router-link to="/transactions" class="btn btn-outline explore-details__link">
        <CreditCard class="w-4 h-4" aria-hidden="true" /> Transactions
      </router-link>
    </nav>

    <TransactionModal
      :show="showDailyModal"
      kind="date"
      :show-date-column="true"
      :hide-category-visuals="false"
      :subtitle="dailyModalSubtitle"
      :transactions="dailyModalTransactions"
      @close="closeModal('daily')"
    />
    <TransactionModal
      :show="showCategoryModal"
      :kind="categoryModalKind"
      :show-date-column="true"
      :hide-category-visuals="true"
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
import TopAccountSnapshot from '@/components/widgets/TopAccountSnapshot.vue'
import SkeletonCard from '@/components/ui/SkeletonCard.vue'
import api from '@/services/api'
import { uniqueReconnectConnections } from '@/utils/plaidConnectionStatus'
import { formatDateInput, useDateRange, getChartPresetRange, CHART_RANGE_PRESETS } from '@/composables/useDateRange'
import { fetchTransactions as fetchTransactionsApi } from '@/api/transactions'
import { fetchCategoryTransactions, fetchMerchantTransactions } from '@/api/charts'
import { useCategories } from '@/composables/useCategories'
import { useDashboardModals } from '@/composables/useDashboardModals'

const DASHBOARD_ACCOUNT_SYNC_STORAGE_KEY = 'dashboard:last-account-sync-at'
const DASHBOARD_ACCOUNT_SYNC_INTERVAL_MS = 30 * 60 * 1000
const IS_TEST_MODE = import.meta.env.MODE === 'test'
let dashboardAccountSyncStorageAvailable = true

/* Async components */
const NetOverviewSection = defineAsyncComponent(
  () => import('@/components/dashboard/NetOverviewSection.vue'),
)
const CategoryBreakdownSection = defineAsyncComponent(
  () => import('@/components/dashboard/CategoryBreakdownSection.vue'),
)
const InsightsRow = defineAsyncComponent(() => import('@/components/dashboard/InsightsRow.vue'))

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
const categoryModalKind = ref('category')
const plaidUserId = import.meta.env.VITE_USER_ID_PLAID || ''
const currentDate = new Date().toLocaleDateString(undefined, {
  month: 'long',
  day: 'numeric',
  year: 'numeric',
})
const loadErrorMessage = ref('')
const activityStatusMessage = ref('')
const reconnectCount = ref(0)

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
/** Last quick preset applied (mtd | rolling_30); the active period is `selectedPreset`. */
const netTimeframe = ref('mtd')
/** Which period control produced the visible dates: mtd | rolling_30 | custom. */
const selectedPreset = ref('mtd')
const safeToSpend = ref(null)
const safeToSpendLoading = ref(false)
const safeToSpendError = ref('')
const safeToSpendMode = ref('today')
let activeLoadToken = 0
let safeToSpendToken = 0

/**
 * Build the visible dashboard period for a quick preset, ending today.
 *
 * @param {'mtd'|'rolling_30'} mode - Preset to resolve.
 * @param {Date} [now] - Reference date.
 * @returns {{ start: string; end: string }} Inclusive date boundaries.
 */
function getPresetRange(mode, now = new Date()) {
  return getChartPresetRange(mode, now)
}

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
    // Month-to-date: the dashboard never defaults to future days.
    initialRange: getPresetRange('mtd'),
    onDebouncedChange: onDateRangeChange,
  })

/**
 * Apply a quick period preset. Picker values, chart range, and preset state
 * change together so the controls cannot disagree with the chart.
 *
 * @param {'mtd'|'rolling_30'} mode - Preset to apply.
 */
function setDashboardPeriodPreset(mode) {
  if (!CHART_RANGE_PRESETS.some((option) => option.value === mode)) return
  const range = getPresetRange(mode)
  dateRange.value = { ...range }
  debouncedRange.value = { ...range }
  netTimeframe.value = mode
  selectedPreset.value = mode
}

function setManualStartDate(value) {
  dateRange.value.start = value
  netTimeframe.value = 'custom'
  selectedPreset.value = 'custom'
}

function setManualEndDate(value) {
  dateRange.value.end = value
  netTimeframe.value = 'custom'
  selectedPreset.value = 'custom'
}

const reviewTagFilter = ref('')
const normalizedReviewTag = computed(() => reviewTagFilter.value.trim())
/** Count of ALL transactions in the selected period (there is no reviewed status yet). */
const periodTransactionCount = ref(0)
const periodTransactionCountLoading = ref(false)
const periodTransactionCountError = ref(false)
let periodTransactionCountToken = 0

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

async function loadPeriodTransactionCount(filters = reviewFilters.value) {
  const token = ++periodTransactionCountToken
  periodTransactionCountLoading.value = true
  periodTransactionCountError.value = false

  try {
    const result = await fetchTransactionsApi({
      page: 1,
      page_size: 1,
      ...filters,
    })
    if (token !== periodTransactionCountToken) return
    const total = Number(result.total ?? result.total_count ?? result.count ?? 0)
    periodTransactionCount.value = Number.isFinite(total) ? total : 0
  } catch (error) {
    if (token !== periodTransactionCountToken) return
    console.error('Failed to load period transaction count', error)
    periodTransactionCountError.value = true
    periodTransactionCount.value = 0
  } finally {
    if (token === periodTransactionCountToken) {
      periodTransactionCountLoading.value = false
    }
  }
}

/**
 * Refresh the safe-to-spend decision card for the selected horizon.
 *
 * @returns {Promise<void>} Resolves when guidance is loaded or an inline error is set.
 */
async function loadSafeToSpend() {
  const token = ++safeToSpendToken
  safeToSpendLoading.value = true
  safeToSpendError.value = ''

  try {
    const result = await api.fetchSafeToSpend({
      mode: safeToSpendMode.value,
      user_id: plaidUserId || undefined,
    })
    if (token !== safeToSpendToken) return
    if (result?.status === 'success') {
      safeToSpend.value = result.data
    } else {
      safeToSpendError.value = result?.message || 'Unable to calculate spend room.'
    }
  } catch (error) {
    if (token !== safeToSpendToken) return
    console.error('Failed to load safe-to-spend guidance:', error)
    safeToSpendError.value =
      error?.response?.data?.message || error?.message || 'Unable to calculate spend room.'
  } finally {
    if (token === safeToSpendToken) {
      safeToSpendLoading.value = false
    }
  }
}

function setSafeToSpendMode(mode) {
  safeToSpendMode.value = mode
  loadSafeToSpend()
}

/**
 * Perform the dashboard's data load in parallel so breakdown options, activity
 * status, and decision guidance all start with fresh data. Applies a shared
 * fallback message when any fetch fails. The optional range argument enables
 * debounced refreshes without overlapping the results from earlier requests.
 * The period transaction count is loaded by the `reviewFilters` watcher.
 *
 * @param {{ start: string; end: string }} [range] - Date boundaries to apply to
 *   option requests.
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
    const [categoriesResult, activityStatusResult] = await Promise.all([
      refreshOptions(params).catch(recordFailure),
      api.fetchDashboardActivityStatus(params).catch(recordFailure),
      loadSafeToSpend().catch(recordFailure),
    ])

    if (loadToken !== activeLoadToken) {
      return
    }

    const hadFailure = [categoriesResult, activityStatusResult].some(
      (result) => result && '__error' in result,
    )

    if (activityStatusResult?.status === 'success' && activityStatusResult.data?.message) {
      activityStatusMessage.value = activityStatusResult.data.message
    } else {
      activityStatusMessage.value = ''
    }

    if (hadFailure) {
      loadErrorMessage.value = fallback
    }
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    loadErrorMessage.value = fallback
  }
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

  const transactions = await fetchCategoryTransactions({
    category_ids: ids,
    start_date: start,
    end_date: end,
  })
  categoryModalTransactions.value = transactions
  categoryModalSubtitle.value = label // Focus on category label in header; dates live in table.
  categoryModalSubtitlePrefix.value = 'Category'
  categoryModalKind.value = 'category'
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

  const transactions = await fetchMerchantTransactions({
    merchant: merchantId,
    start_date: start,
    end_date: end,
  })

  categoryModalTransactions.value = transactions
  categoryModalSubtitle.value = label
  categoryModalSubtitlePrefix.value = 'Merchant'
  categoryModalKind.value = 'merchant'
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
  if (typeof localStorage === 'undefined' || !dashboardAccountSyncStorageAvailable) return 0

  try {
    return Number(localStorage.getItem(DASHBOARD_ACCOUNT_SYNC_STORAGE_KEY) || 0)
  } catch {
    dashboardAccountSyncStorageAvailable = false
    return 0
  }
}

function setStoredDashboardAccountSyncAt(timestamp = Date.now()) {
  if (typeof localStorage === 'undefined' || !dashboardAccountSyncStorageAvailable) return

  try {
    localStorage.setItem(DASHBOARD_ACCOUNT_SYNC_STORAGE_KEY, String(timestamp))
  } catch {
    dashboardAccountSyncStorageAvailable = false
    // Ignore storage errors and keep the dashboard usable.
  }
}

async function maybeAutoSyncAccounts() {
  await refreshPersistedConnectionHealth()
  if (IS_TEST_MODE || !plaidUserId || !dashboardAccountSyncStorageAvailable) return

  const lastSyncAt = getStoredDashboardAccountSyncAt()
  if (Date.now() - lastSyncAt < DASHBOARD_ACCOUNT_SYNC_INTERVAL_MS) {
    return
  }

  setStoredDashboardAccountSyncAt()

  try {
    await api.refreshAccounts({ user_id: plaidUserId })
    await loadDashboardData()
    loadPeriodTransactionCount()
    await refreshPersistedConnectionHealth()
  } catch (error) {
    console.error('Failed to auto-sync dashboard accounts:', error)
  }
}

async function refreshPersistedConnectionHealth() {
  try {
    const response = await api.getAccounts()
    reconnectCount.value = uniqueReconnectConnections(response?.accounts || []).length
  } catch (error) {
    console.error('Failed to load persisted Plaid connection health:', error)
  }
}

onMounted(() => {
  loadDashboardData()
  maybeAutoSyncAccounts()
})
watch(reviewFilters, (filters) => loadPeriodTransactionCount(filters), { immediate: true })

/**
 * The modal manager in `useDashboardModals` keeps overlays mutually exclusive so
 * chart interactions cannot stack dialogs or expanded panels.
 */
</script>

<style scoped>
.dashboard-skeleton-panel {
  box-shadow: var(--depth-inner-glow), var(--depth-shadow-resting);
}

.explore-details {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.explore-details__label {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-right: 0.25rem;
}

.explore-details__link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
</style>
