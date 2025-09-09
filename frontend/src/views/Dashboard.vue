<!--
  Dashboard.vue
  Main application dashboard showing snapshots, charts, and financial summaries.
-->
<template>
  <AppLayout>
    <BasePageLayout gap="gap-8">
      <!-- WELCOME HEADER CARD -->
      <div
        class="h-3 w-full rounded bg-gradient-to-r from-[var(--color-accent-cyan)] via-[var(--color-accent-purple)] to-[var(--color-accent-magenta)] mb-6"
      ></div>
      <div
        class="w-full mb-8 bg-[var(--color-bg-sec)] border-2 border-[var(--color-accent-cyan)] rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-2"
      >
        <h1
          class="text-4xl md:text-5xl font-extrabold tracking-wide text-[var(--color-accent-cyan)] mb-2 drop-shadow"
        >
          Welcome, <span class="username">{{ userName }}</span
          >!
        </h1>
        <p class="text-lg text-muted">Today is {{ currentDate }}</p>
        <p class="italic text-muted">{{ netWorthMessage }}</p>
      </div>
      <div
        class="h-3 w-full rounded bg-gradient-to-r from-[var(--color-accent-cyan)] via-[var(--color-accent-purple)] to-[var(--color-accent-magenta)] mb-6"
      ></div>
      <div class="flex justify-end mb-4">
        <DateRangeSelector
          v-model:start-date="dateRange.start"
          v-model:end-date="dateRange.end"
          v-model:zoomed-out="zoomedOut"
        />
      </div>
      <!-- TOP ROW: Top Accounts Snapshot & Net Income -->
      <div class="grid grid-cols-1 gap-6 md:grid-cols-3 items-stretch">
        <!-- Top Accounts Snapshot Card -->
        <div
          class="col-span-1 bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-green)] p-6 flex flex-col gap-4"
        >
          <h2 class="text-2xl font-bold text-[var(--color-accent-green)] text-center">
            Top Accounts
          </h2>
          <TopAccountSnapshot :groups="groups" v-model:active-group="activeGroupId" />
        </div>
        <!-- Net Income Summary Card -->
        <div
          class="md:col-span-2 bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-cyan)] p-6 flex flex-col gap-3"
        >
          <div class="flex items-center justify-center mb-4">
            <h2 class="daily-net-chart-title">
              <span class="title-text">Net Income</span>
              <span class="title-subtitle">(Daily)</span>
            </h2>
          </div>
          <ChartControls
            v-model:show7-day="show7Day"
            v-model:show30-day="show30Day"
            v-model:show-avg-income="showAvgIncome"
            v-model:show-avg-expenses="showAvgExpenses"
          />

          <DailyNetChart
            :start-date="dateRange.start"
            :end-date="dateRange.end"
            :zoomed-out="zoomedOut"
            :show7-day="show7Day"
            :show30-day="show30Day"
            :show-avg-income="showAvgIncome"
            :show-avg-expenses="showAvgExpenses"
            @summary-change="netSummary = $event"
            @data-change="chartData = $event"
            @bar-click="onNetBarClick"
          />
        </div>
      </div>

      <!-- FINANCIAL SUMMARY ROW -->
      <div
        class="bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-cyan)] p-6"
      >
        <FinancialSummary :summary="netSummary" :chart-data="chartData" :zoomed-out="zoomedOut" />
      </div>

      <!-- SPENDING ROW: Category Chart & Insights -->
      <div class="grid grid-cols-1 gap-6 md:grid-cols-3 items-stretch">
        <!-- Category Spending -->
        <div
          class="md:col-span-2 w-full bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-yellow)] p-6 flex flex-col gap-3 overflow-hidden"
        >
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-xl font-bold text-[var(--color-accent-yellow)]">
              Spending by Category
            </h2>
            <ChartWidgetTopBar>
              <template #controls>
                <GroupedCategoryDropdown
                  :groups="categoryGroups"
                  :modelValue="catSelected"
                  @update:modelValue="onCatSelected"
                  class="ml-2 w-full md:w-64"
                />
                <button class="btn btn-outline hover-lift ml-2" @click="groupOthers = !groupOthers">
                  {{ groupOthers ? 'Expand All' : 'Consolidate Minor Categories' }}
                </button>
              </template>
            </ChartWidgetTopBar>
          </div>
          <CategoryBreakdownChart
            :start-date="dateRange.start"
            :end-date="dateRange.end"
            :selected-category-ids="catSelected"
            :group-others="groupOthers"
            @summary-change="catSummary = $event"
            @categories-change="allCategoryIds = $event"
            @bar-click="onCategoryBarClick"
          />

          <div class="mt-1">
            <span class="font-bold">Total:</span>
            <span class="ml-1 text-[var(--color-accent-cyan)] font-bold">{{
              formatAmount(catSummary.total)
            }}</span>
          </div>
        </div>
        <SpendingInsights />
      </div>

      <!-- RESERVED TABLES PANEL -->
      <div
        class="relative min-h-[440px] bg-[var(--color-bg-sec)] border-2 border-[var(--color-accent-cyan)] rounded-2xl shadow-xl flex flex-col justify-center items-stretch overflow-hidden"
      >
        <!-- Button row: Show only if neither table is expanded -->
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
            <div class="mx-8 text-lg font-light text-muted select-none">or</div>
            <button
              @click="expandTransactions"
              class="flex-1 text-2xl font-bold px-8 py-8 rounded-2xl border-2 border-[var(--color-accent-red)] bg-[var(--color-bg-sec)] shadow-lg hover:bg-[var(--color-accent-red)] hover:text-[var(--color-bg-sec)] transition"
            >
              Expand Transactions Table
            </button>
          </div>
        </transition>
        <!-- Expanded Accounts Table -->
        <transition name="modal-fade-slide">
          <div
            v-if="accountsExpanded"
            class="absolute inset-0 p-8 flex flex-col bg-[var(--color-bg-sec)]"
          >
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-2xl font-bold text-[var(--color-accent-cyan)]">Accounts Table</h2>
              <button
                @click="collapseTables"
                class="px-4 py-2 rounded bg-[var(--color-accent-cyan)] text-[var(--color-bg-sec)] font-bold text-lg shadow hover:brightness-105"
              >
                Close
              </button>
            </div>
            <div class="flex-1 min-h-[300px]">
              <AccountsTable />
            </div>
          </div>
        </transition>
        <!-- Expanded Transactions Table -->
        <transition name="modal-fade-slide">
          <div
            v-if="transactionsExpanded"
            class="absolute inset-0 p-8 flex flex-col bg-[var(--color-bg-sec)]"
          >
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-2xl font-bold text-[var(--color-accent-red)]">Transactions Table</h2>
              <button
                @click="collapseTables"
                class="px-4 py-2 rounded bg-[var(--color-accent-red)] text-[var(--color-bg-sec)] font-bold text-lg shadow hover:brightness-105"
              >
                Close
              </button>
            </div>
            <div class="flex-1 min-h-[300px]">
              <TransactionsTable
                :transactions="filteredTransactions"
                :sort-key="sortKey"
                :sort-order="sortOrder"
                :search="searchQuery"
                @sort="setSort"
                :current-page="currentPage"
                :total-pages="totalPages"
                @change-page="changePage"
              />
              <PaginationControls
                :current-page="currentPage"
                :total-pages="totalPages"
                @change-page="changePage"
              />
            </div>
          </div>
        </transition>
      </div>

      <TransactionModal
        :show="showModal"
        :subtitle="modalSubtitle"
        :transactions="modalTransactions"
        :kind="modalKind"
        :show-date-column="modalShowDate"
        :hide-category-visuals="modalHideCategoryVisuals"
        @close="showModal = false"
      />
    </BasePageLayout>

    <template #footer> &copy; {{ new Date().getFullYear() }} braydio • pyNance. </template>
  </AppLayout>
</template>

<script setup>
// Dashboard view showing financial charts and transaction tables.
import AppLayout from '@/components/layout/AppLayout.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import CategoryBreakdownChart from '@/components/charts/CategoryBreakdownChart.vue'
import ChartWidgetTopBar from '@/components/ui/ChartWidgetTopBar.vue'
import ChartControls from '@/components/ChartControls.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'
import AccountsTable from '@/components/tables/AccountsTable.vue'
import TransactionsTable from '@/components/tables/TransactionsTable.vue'
import PaginationControls from '@/components/tables/PaginationControls.vue'
import TransactionModal from '@/components/modals/TransactionModal.vue'
import TopAccountSnapshot from '@/components/widgets/TopAccountSnapshot.vue'
import GroupedCategoryDropdown from '@/components/ui/GroupedCategoryDropdown.vue'
import FinancialSummary from '@/components/statistics/FinancialSummary.vue'
import SpendingInsights from '@/components/SpendingInsights.vue'
import { formatAmount } from '@/utils/format'
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'
import { useTransactions } from '@/composables/useTransactions.js'
import { fetchCategoryTree } from '@/api/categories'
import { fetchTransactions } from '@/api/transactions'
import { useAccountGroups } from '@/composables/useAccountGroups'

// Transactions and user
const {
  searchQuery,
  currentPage,
  totalPages,
  filteredTransactions,
  sortKey,
  sortOrder,
  setSort,
  changePage,
} = useTransactions(15)
const showModal = ref(false)
const modalTransactions = ref([])
const modalSubtitle = ref('')
const modalKind = ref('date')
const modalShowDate = ref(false)
const modalHideCategoryVisuals = ref(false)
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
const { groups, activeGroupId } = useAccountGroups()

onMounted(async () => {
  try {
    const res = await api.fetchNetAssets()
    if (res.status === 'success' && Array.isArray(res.data) && res.data.length) {
      netWorth.value = res.data[res.data.length - 1].net_assets
    }
    await loadCategoryGroups()
  } catch (e) {
    console.error('Failed to fetch net assets:', e)
  }
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

// --- SHARED DATE RANGE STATE ---
const today = new Date()
const dateRange = ref({
  start: new Date(today.getFullYear(), today.getMonth(), today.getDate() - 30)
    .toISOString()
    .slice(0, 10),
  end: today.toISOString().slice(0, 10),
})

const catSummary = ref({ total: 0, startDate: '', endDate: '' })
const catSelected = ref([]) // user selected
const allCategoryIds = ref([]) // from chart data
const defaultSet = ref(false) // only auto-select ONCE per data load
const groupOthers = ref(true) // aggregate small categories

// When CategoryBreakdownChart fetches, auto-select the first 5 categories once
// per fetch. Includes "Other" when grouping is enabled and does not repopulate
// on clear.
watch(allCategoryIds, (ids) => {
  if ((!catSelected.value || !catSelected.value.length) && ids.length && !defaultSet.value) {
    catSelected.value = ids.slice(0, 5)
    defaultSet.value = true
  }
})

const accountsExpanded = ref(false)
const transactionsExpanded = ref(false)
function expandAccounts() {
  accountsExpanded.value = true
  transactionsExpanded.value = false
}
function expandTransactions() {
  transactionsExpanded.value = true
  accountsExpanded.value = false
}
function collapseTables() {
  accountsExpanded.value = false
  transactionsExpanded.value = false
}

// When user clears selection, do NOT re-select (unless new data is fetched)
function onCatSelected(newIds) {
  catSelected.value = Array.isArray(newIds) ? newIds : [newIds]
}

// When user changes date range, clear selections so next data load re-applies auto-select
watch(
  () => [dateRange.value.start, dateRange.value.end],
  () => {
    catSelected.value = []
    defaultSet.value = false
  },
)

// When grouping mode changes, allow auto-select on next fetch
watch(groupOthers, () => {
  defaultSet.value = false
})

// For dropdown: fetch full tree for grouped dropdown (not just breakdown result)
const categoryGroups = ref([])

/**
 * Fetch the full category tree and transform it into groups for the
 * dropdown component.
 */
async function loadCategoryGroups() {
  try {
    const res = await fetchCategoryTree()
    if (res.status === 'success' && Array.isArray(res.data)) {
      // res.data is confirmed to be an array, so no fallback is required
      categoryGroups.value = res.data
        .map((root) => ({
          id: root.id,
          label: root.label,
          children: (root.children || []).map((c) => ({
            id: c.id,
            label: c.label ?? c.name,
          })),
        }))
        .sort((a, b) => a.label.localeCompare(b.label))
    }
  } catch {
    categoryGroups.value = []
  }
}

// Handle clicks on the DailyNetChart bars and open a modal for that date.
async function onNetBarClick(label) {
  const result = await fetchTransactions({ start_date: label, end_date: label })
  modalTransactions.value = result.transactions || []
  // Configure modal for date mode
  modalKind.value = 'date'
  modalShowDate.value = false
  modalHideCategoryVisuals.value = false
  modalSubtitle.value = label
  showModal.value = true
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
  if (!ids.length) return

  // Determine the date range in effect for the category chart. The chart emits
  // `summary-change` events that populate `catSummary` with the actual start
  // and end dates used in its query. This ensures the modal reflects the same
  // range, even if it differs from the user-selected inputs.
  const start = catSummary.value.startDate || dateRange.value.start
  const end = catSummary.value.endDate || dateRange.value.end

  const result = await fetchTransactions({
    category_ids: ids,
    start_date: start,
    end_date: end,
  })
  modalTransactions.value = result.transactions || []

  // Configure modal for category mode
  modalKind.value = 'category'
  modalShowDate.value = true
  modalHideCategoryVisuals.value = true

  // Focus on category label only in header; dates move to table
  modalSubtitle.value = label
  showModal.value = true
}
</script>

<style scoped>
@import '../assets/css/main.css';

.dashboard-outer {
  /* Vertically and horizontally center, with a max width for the dashboard content */
  min-height: 100vh;
  width: 100vw;
  background: var(--theme-bg);
}

.username {
  @apply text-[var(--color-accent-cyan)] text-lg;
  text-shadow: 2px 6px 8px var(--bar-gradient-end);
}

.text-muted {
  color: var(--color-text-muted);
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  max-height: 0;
  transform: scaleY(0.9);
}

.fade-enter-to,
.fade-leave-from {
  opacity: 1;
  max-height: 999px;
  transform: scaleY(1);
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: scaleY(0.95);
}

.fade-enter-to,
.fade-leave-from {
  opacity: 1;
  transform: scaleY(1);
}

/* Dashboard Control Button Styles */

/* Daily Net Chart Title Styles */
.daily-net-chart-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-align: center;
}

.title-icon {
  font-size: 1.2rem;
  filter: drop-shadow(0 0 8px rgba(113, 156, 214, 0.6));
  animation: subtle-glow 3s ease-in-out infinite alternate;
}

.title-text {
  background: linear-gradient(135deg, var(--color-accent-cyan) 0%, var(--color-accent-blue) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 20px rgba(113, 156, 214, 0.3);
}

.title-subtitle {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  font-weight: 500;
  opacity: 0.8;
}

@keyframes subtle-glow {
  0% {
    filter: drop-shadow(0 0 8px rgba(113, 156, 214, 0.6));
  }
  100% {
    filter: drop-shadow(0 0 12px rgba(113, 156, 214, 0.8));
  }
}
</style>
