<!--
  Dashboard.vue
  Main application dashboard showing snapshots, charts, and financial summaries.
-->
<template>
  <AppLayout>
    <div class="container">
      <!-- WELCOME HEADER CARD -->
      <div class="w-20 h-3 rounded bg-gradient-to-r from-[var(--color-accent-cyan)] via-[var(--color-accent-purple)] to-[var(--color-accent-magenta)] mb-6"></div>
      <div class="flex justify-center mb-8">
        <div
          class="w-full max-w-3xl bg-[var(--color-bg-sec)] border-2 border-[var(--color-accent-cyan)] rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-2">
          <h1 class="text-4xl md:text-5xl font-extrabold tracking-wide text-[var(--color-accent-cyan)] mb-2 drop-shadow">Welcome, <span
              class="username">{{ userName }}</span>!</h1>
        <p class="text-lg text-muted">Today is {{ currentDate }}</p>
        <p class="italic text-muted">{{ netWorthMessage }}</p>
      </div>
      </div>
      <div class="w-20 h-3 rounded bg-gradient-to-r from-[var(--color-accent-cyan)] via-[var(--color-accent-purple)] to-[var(--color-accent-magenta)] mb-6"></div>
      <div class="dashboard-content flex flex-col gap-8 w-full max-w-7xl mx-auto px-2">
      <!-- TOP ROW: Top Accounts Snapshot & Net Income -->
      <div class="flex flex-col md:flex-row gap-6 justify-center items-stretch">
        <!-- Top Accounts Snapshot Card -->
        <div
          class="flex-1 min-w-[340px] max-w-[400px] bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-green)] p-6 flex flex-col justify-between">
          <h2 class="text-2xl font-bold mb-4 text-[var(--color-accent-green)] text-center">Top Accounts</h2>
          <TopAccountSnapshot use-spectrum />
        </div>
        <!-- Net Income Summary Card -->
        <div
          class="flex-[2_2_0%] min-w-[360px] max-w-[750px] bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-cyan)] p-6 flex flex-col gap-3">
          <div class="flex items-center justify-center mb-4">
            <div class="flex-1 flex justify-center">
              <h2 class="daily-net-chart-title">
                <span class="title-text">Net Income</span>
                <span class="title-subtitle">(Daily)</span>
              </h2>
            </div>
            <div class="flex-shrink-0">
              <ChartWidgetTopBar>
                <template #controls>
                  <button
                    class="dashboard-control-btn dashboard-control-btn-primary"
                    @click="zoomedOut = !zoomedOut">
                    {{ zoomedOut ? 'Zoom In' : 'Zoom Out' }}
                  </button>
                </template>
              </ChartWidgetTopBar>
            </div>
          </div>
          <DailyNetChart :zoomed-out="zoomedOut" @summary-change="netSummary = $event" @data-change="chartData = $event" @bar-click="onNetBarClick" />
        </div>
      </div>

      <!-- FINANCIAL SUMMARY ROW -->
      <div class="bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-cyan)] p-6">
        <FinancialSummary
          :summary="netSummary"
          :chart-data="chartData"
          :zoomed-out="zoomedOut"
        />
      </div>

      <!-- SPENDING ROW: Category Chart & Insights -->
      <div class="flex flex-col md:flex-row gap-6 justify-center items-stretch">
        <!-- Category Spending -->
        <div
          class="flex-[2_2_0%] min-w-[360px] max-w-[750px] bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-yellow)] p-6 flex flex-col gap-3">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-xl font-bold text-[var(--color-accent-yellow)]">Spending by Category</h2>
            <ChartWidgetTopBar>
              <template #controls>
                  <input type="date" v-model="catRange.start"
                    class="date-picker px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)] focus:ring-2 focus:ring-[var(--color-accent-cyan)]" />
                  <input type="date" v-model="catRange.end"
                    class="date-picker px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)] focus:ring-2 focus:ring-[var(--color-accent-cyan)] ml-2" />
                <GroupedCategoryDropdown :groups="categoryGroups" :modelValue="catSelected"
                  @update:modelValue="onCatSelected" class="w-64 ml-2" />
                <button
                  class="dashboard-control-btn dashboard-control-btn-secondary ml-2"
                  @click="groupOthers = !groupOthers"
                >
                  {{ groupOthers ? 'Show All' : 'Group Others' }}
                </button>
              </template>
            </ChartWidgetTopBar>
          </div>
          <CategoryBreakdownChart :start-date="catRange.start" :end-date="catRange.end"
            :selected-category-ids="catSelected" :group-others="groupOthers"
            @summary-change="catSummary = $event" @categories-change="allCategoryIds = $event"
            @bar-click="onCategoryBarClick" />
          <div class="mt-1">
            <span class="font-bold">Total:</span>
              <span class="ml-1 text-[var(--color-accent-cyan)] font-bold">{{ formatAmount(catSummary.total) }}</span>
          </div>
        </div>
        <!-- Spending Insights Placeholder -->
        <div
          class="flex-1 min-w-[340px] max-w-[400px] bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-magenta)] p-6 flex flex-col items-center justify-center">
          <h2 class="text-xl font-bold text-[var(--color-accent-magenta)] mb-4">Spending Insights</h2>
          <p class="italic text-muted text-center">More detailed insights coming soon...</p>
        </div>
      </div>

      <!-- RESERVED TABLES PANEL -->
        <div
          class="relative min-h-[440px] bg-[var(--color-bg-sec)] border-2 border-[var(--color-accent-cyan)] rounded-2xl shadow-xl flex flex-col justify-center items-stretch overflow-hidden">
        <!-- Button row: Show only if neither table is expanded -->
          <div v-if="!accountsExpanded && !transactionsExpanded"
            class="flex flex-row justify-between items-center gap-8 w-full h-full p-12">
            <button @click="expandAccounts"
              class="flex-1 text-2xl font-bold px-8 py-8 rounded-2xl border-2 border-[var(--color-accent-cyan)] bg-[var(--color-bg-sec)] shadow-lg hover:bg-[var(--color-accent-cyan)] hover:text-[var(--color-bg-sec)] transition">
              Expand Accounts Table
            </button>
            <div class="mx-8 text-lg font-light text-muted select-none">or</div>
            <button @click="expandTransactions"
              class="flex-1 text-2xl font-bold px-8 py-8 rounded-2xl border-2 border-[var(--color-accent-red)] bg-[var(--color-bg-sec)] shadow-lg hover:bg-[var(--color-accent-red)] hover:text-[var(--color-bg-sec)] transition">
              Expand Transactions Table
            </button>
          </div>
        <!-- Expanded Accounts Table -->
        <transition name="fade">
          <div v-if="accountsExpanded" class="absolute inset-0 p-8 flex flex-col bg-[var(--color-bg-sec)]">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-2xl font-bold text-[var(--color-accent-cyan)]">Accounts Table</h2>
              <button @click="collapseTables"
                  class="px-4 py-2 rounded bg-[var(--color-accent-cyan)] text-[var(--color-bg-sec)] font-bold text-lg shadow hover:brightness-105">
                Close
              </button>
            </div>
            <div class="flex-1 min-h-[300px]">
              <AccountsTable />
            </div>
          </div>
        </transition>
        <!-- Expanded Transactions Table -->
        <transition name="fade">
          <div v-if="transactionsExpanded" class="absolute inset-0 p-8 flex flex-col bg-[var(--color-bg-sec)]">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-2xl font-bold text-[var(--color-accent-red)]">Transactions Table</h2>
                <button @click="collapseTables"
                  class="px-4 py-2 rounded bg-[var(--color-accent-red)] text-[var(--color-bg-sec)] font-bold text-lg shadow hover:brightness-105">
                Close
              </button>
            </div>
            <div class="flex-1 min-h-[300px]">
              <TransactionsTable :transactions="filteredTransactions" :sort-key="sortKey" :sort-order="sortOrder"
                :search="searchQuery" @sort="setSort" :current-page="currentPage" :total-pages="totalPages"
                @change-page="changePage" />
              <PaginationControls :current-page="currentPage" :total-pages="totalPages" @change-page="changePage" />
            </div>
          </div>
        </transition>
      </div>

      <TransactionModal :show="showModal" :subtitle="modalSubtitle" :transactions="modalTransactions"
        @close="showModal = false" />
    </div>

    <template #footer>
      &copy; {{ new Date().getFullYear() }} braydio • pyNance.
    </template>
  </AppLayout>
</template>



<script setup>
// Dashboard view showing financial charts and transaction tables.
import AppLayout from '@/components/layout/AppLayout.vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import CategoryBreakdownChart from '@/components/charts/CategoryBreakdownChart.vue'
import ChartWidgetTopBar from '@/components/ui/ChartWidgetTopBar.vue'
import AccountsTable from '@/components/tables/AccountsTable.vue'
import TransactionsTable from '@/components/tables/TransactionsTable.vue'
import PaginationControls from '@/components/tables/PaginationControls.vue'
import TransactionModal from '@/components/modals/TransactionModal.vue'
import TopAccountSnapshot from '@/components/widgets/TopAccountSnapshot.vue'
import GroupedCategoryDropdown from '@/components/ui/GroupedCategoryDropdown.vue'
import FinancialSummary from '@/components/statistics/FinancialSummary.vue'
import { formatAmount } from '@/utils/format'
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'
import { useTransactions } from '@/composables/useTransactions.js'
import { fetchCategoryTree } from '@/api/categories'
import { fetchTransactions } from '@/api/transactions'

// Transactions and user
const {
  searchQuery,
  currentPage,
  totalPages,
  filteredTransactions,
  sortKey,
  sortOrder,
  setSort,
  changePage
} = useTransactions(15)
const showModal = ref(false)
const modalTransactions = ref([])
const modalSubtitle = ref('')
const userName = import.meta.env.VITE_USER_ID_PLAID || 'Guest'
const currentDate = new Date().toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })
const netWorth = ref(0)
const netWorthMessage = computed(() => {
  if (netWorth.value < 0) return "... and things are looking quite bleak."
  if (netWorth.value > 1000) return "Ahh... well in the black."
  return "Uhh... keep up the... whatever this is."
})

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
  aboveAvgIncomeDays: 0,
  aboveAvgExpenseDays: 0,
})
const chartData = ref([])
const zoomedOut = ref(false)

// --- CATEGORY BREAKDOWN STATE ---
const today = new Date()
const catRange = ref({
  start: new Date(today.getFullYear(), today.getMonth(), today.getDate() - 30).toISOString().slice(0, 10),
  end: new Date().toISOString().slice(0, 10)
})

const catSummary = ref({ total: 0, startDate: '', endDate: '' })
const catSelected = ref([])           // user selected
const allCategoryIds = ref([])        // from chart data
const defaultSet = ref(false)         // only auto-select ONCE per data load
const groupOthers = ref(true)         // aggregate small categories

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

// When user changes date range, let next data load re-apply auto-select
watch(() => [catRange.value.start, catRange.value.end], () => {
  defaultSet.value = false
})

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
        .map(root => ({
          id: root.id,
          label: root.label,
          children: (root.children || []).map(c => ({
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
  // Show the selected date prominently in the modal header
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
  const { label, ids = [] } =
    typeof payload === 'object' ? payload : { label: payload, ids: [] }

  // Only display the modal when the clicked bar corresponds to selected categories
  if (!ids.length) return

  // Determine the date range in effect for the category chart. The chart emits
  // `summary-change` events that populate `catSummary` with the actual start
  // and end dates used in its query. This ensures the modal reflects the same
  // range, even if it differs from the user-selected inputs.
  const start = catSummary.value.startDate || catRange.value.start
  const end = catSummary.value.endDate || catRange.value.end

  const result = await fetchTransactions({
    category_ids: ids,
    start_date: start,
    end_date: end,
  })
  modalTransactions.value = result.transactions || []

  // Display the category label and date span in the modal header
  modalSubtitle.value = `${label}: ${start} – ${end}`
  showModal.value = true
}
</script>

<style scoped>
@import "../assets/css/main.css";

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

dashboard-content {
  max-width: 90vw;
}

@media (max-width: 768px) {
  .dashboard-content {
    padding-left: 0.5rem;
    padding-right: 0.5rem;
    gap: 1.5rem;
  }
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
.dashboard-control-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 0.6rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.025em;
  text-transform: none;
}

  .dashboard-control-btn-primary {
    background: linear-gradient(135deg, var(--color-bg-sec) 0%, var(--color-bg-dark) 100%);
    border: 1.5px solid var(--color-accent-cyan);
    color: var(--color-accent-cyan);
  }

  .dashboard-control-btn-primary:hover {
    background: linear-gradient(135deg, var(--color-accent-cyan) 0%, var(--color-accent-blue) 100%);
    color: var(--color-bg-dark);
    border-color: var(--color-accent-cyan);
    box-shadow: 0 6px 20px rgba(113, 156, 214, 0.4);
    transform: translateY(-2px);
  }

.dashboard-control-btn-secondary {
  background: linear-gradient(135deg, var(--color-bg-sec) 0%, var(--color-bg-dark) 100%);
  border: 1.5px solid var(--color-accent-yellow);
  color: var(--color-accent-yellow);
}

  .dashboard-control-btn-secondary:hover {
    background: linear-gradient(135deg, var(--color-accent-yellow) 0%, var(--color-accent-red) 100%);
    color: var(--color-bg-dark);
    border-color: var(--color-accent-cyan);
    box-shadow: 0 6px 20px rgba(219, 192, 116, 0.4);
    transform: translateY(-2px);
  }

.dashboard-control-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.dashboard-control-btn .btn-icon {
  font-size: 0.8rem;
  opacity: 0.9;
  transition: opacity 0.2s;
}

.dashboard-control-btn:hover .btn-icon {
  opacity: 1;
}

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
