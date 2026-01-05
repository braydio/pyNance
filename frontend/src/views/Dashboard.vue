<!--
  Dashboard.vue
  Main application dashboard showing snapshots, charts, and financial summaries.
-->
<template>
  <AppLayout>
    <BasePageLayout gap="gap-8">
      <NetOverviewSection
        :user-name="userName"
        :current-date="currentDate"
        :net-worth-message="netWorthMessage"
        :date-range="dateRange"
        :debounced-range="debouncedRange"
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
        @net-summary-change="netSummary = $event"
        @net-data-change="chartData = $event"
        @net-bar-click="onNetBarClick"
      />

      <InsightsRow>
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
      </InsightsRow>

      <div
        class="relative min-h-[440px] bg-[var(--color-bg-sec)] border-2 border-[var(--color-accent-cyan)] rounded-2xl shadow-xl flex flex-col justify-center items-stretch overflow-hidden"
      >
        <transition name="accordion">
          <div
            v-if="!accountsExpanded && !transactionsExpanded"
            class="flex flex-row justify-between items-center gap-8 w-full h-full p-12"
          >
            <button
            @click="expandAccounts"
              class="flex-1 text-2xl font-bold px-8 py-8 rounded-2xl border-2 border-[var(--color-accent-cyan)] bg-[var(--color-bg-sec)] shadow-lg hover:bg-[var(--color-accent-cyan)] hover:text-[var(--color-bg-sec)] transition"
            >
              Expand Accounts Table
            </button>
            <div class="mx-8 text-lg font-light text-[var(--color-text-muted)] select-none">or</div>
            <button
              @click="expandTransactions"
              class="flex-1 text-2xl font-bold px-8 py-8 rounded-2xl border-2 border-[var(--color-accent-red)] bg-[var(--color-bg-sec)] shadow-lg hover:bg-[var(--color-accent-red)] hover:text-[var(--color-bg-sec)] transition"
            >
              Expand Transactions Table
            </button>
          </div>
        </transition>
        <transition name="modal-fade-slide">
          <AccountsSection v-if="accountsExpanded" @close="collapseTables" />
        </transition>
        <transition name="modal-fade-slide">
          <TransactionsSection
            v-if="transactionsExpanded"
            :transactions="filteredTransactions"
            :sort-key="sortKey"
            :sort-order="sortOrder"
            :search="searchQuery"
            @sort="setSort"
            :current-page="currentPage"
            :total-pages="totalPages"
            :page-size="pageSize"
            :total-count="totalCount"
            @change-page="changePage"
            @set-page="setPage"
            @close="collapseTables"
          />
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
        :transactions="categoryModalTransactions"
        @close="closeModal('category')"
      />
    </BasePageLayout>

    <template #footer> &copy; {{ new Date().getFullYear() }} braydio • pyNance. </template>
  </AppLayout>
</template>

<script setup>
/**
 * Dashboard view showing financial charts, summaries, and transaction tables.
 */
import AppLayout from '@/components/layout/AppLayout.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import TransactionModal from '@/components/modals/TransactionModal.vue'
import api from '@/services/api'
import { ref, computed, onMounted } from 'vue'
import { useTransactions } from '@/composables/useTransactions.js'
import { useDateRange } from '@/composables/useDateRange'
import { fetchTransactions } from '@/api/transactions'
import { useCategories } from '@/composables/useCategories'
import { useDashboardModals } from '@/composables/useDashboardModals'
import NetOverviewSection from '@/components/dashboard/NetOverviewSection.vue'
import CategoryBreakdownSection from '@/components/dashboard/CategoryBreakdownSection.vue'
import InsightsRow from '@/components/dashboard/InsightsRow.vue'
import AccountsSection from '@/components/dashboard/AccountsSection.vue'
import TransactionsSection from '@/components/dashboard/TransactionsSection.vue'

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
} = useTransactions(pageSize)
// Modal manager
const { visibility, openModal, closeModal, isVisible } = useDashboardModals()
const showDailyModal = isVisible('daily')
const dailyModalTransactions = ref([])
const dailyModalSubtitle = ref('')

// Category modal state
const showCategoryModal = isVisible('category')
const categoryModalTransactions = ref([])
const categoryModalSubtitle = ref('')
const userName = import.meta.env.VITE_USER_ID_PLAID || 'Guest'
const currentDate = new Date().toLocaleDateString(undefined, {
  month: 'long',
  day: 'numeric',
  year: 'numeric',
})
const netWorth = ref(0)
const netWorthMessage = computed(() => {
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
 * Reset spending selections when the date range changes and refresh option data.
 *
 * @param {{ start: string; end: string }} range - Debounced date range boundaries.
 */
async function onDateRangeChange(range) {
  resetSelection()
  await refreshOptions({ start_date: range.start, end_date: range.end })
}

const { dateRange = ref({ start: '', end: '' }), debouncedRange = ref({ start: '', end: '' }) } =
  useDateRange({
    onDebouncedChange: onDateRangeChange,
  })

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
    const result = await fetchTransactions({
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
 * Fetches transactions for the clicked category within the active
 * date range and displays them in a modal dialog. If the clicked bar
 * does not correspond to any user-selected categories, no modal is shown.
 *
 * @param {object|string} payload - Click payload from the chart containing
 *   the bar label and an array of category IDs.
 */
async function onCategoryBarClick(payload) {
  const { label, ids = [] } = typeof payload === 'object' ? payload : { label: payload, ids: [] }

  // Only display the modal when the clicked bar corresponds to selected categories
  if (!ids.length || breakdownType.value === 'merchant') return

  // Determine the date range in effect for the category chart. The chart emits
  // `summary-change` events that populate `catSummary` with the actual start
  // and end dates used in its query. This ensures the modal reflects the same
  // range, even if it differs from the user-selected inputs.
  const start = catSummary.value.startDate || debouncedRange.value.start
  const end = catSummary.value.endDate || debouncedRange.value.end

  const result = await fetchTransactions({
    category_ids: ids,
    start_date: start,
    end_date: end,
  })
  categoryModalTransactions.value = result.transactions || []
  categoryModalSubtitle.value = label // Focus on category label in header; dates live in table.
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

onMounted(async () => {
  try {
    const res = await api.fetchNetAssets()
    if (res.status === 'success' && Array.isArray(res.data) && res.data.length) {
      netWorth.value = res.data[res.data.length - 1].net_assets
    }
    await refreshOptions({
      start_date: debouncedRange.value.start,
      end_date: debouncedRange.value.end,
    })
  } catch (e) {
    console.error('Failed to fetch net assets:', e)
  }
})

/**
 * The modal manager in `useDashboardModals` keeps overlays mutually exclusive so
 * chart interactions cannot stack dialogs or expanded panels.
 */
</script>
