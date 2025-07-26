<template>
  <AppLayout>
    <!-- WELCOME HEADER CARD -->
    <div class="w-20 h-3 rounded bg-[var(--color-accent-ice)] mb-6"></div>
    <div class="flex justify-center mb-8">
      <div
        class="w-full max-w-3xl bg-[var(--color-bg-sec)] border-2 border-[var(--color-accent-mint)] rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-2">
        <h1 class="text-4xl md:text-5xl font-extrabold tracking-wide text-accent-ice mb-2 drop-shadow">Welcome, <span
            class="username">{{ userName }}</span>!</h1>
        <p class="text-lg text-muted">Today is {{ currentDate }}</p>
        <p class="italic text-muted">{{ netWorthMessage }}</p>
      </div>

    </div>
    <div class="w-20 h-3 rounded bg-[var(--color-accent-ice)] mb-6"></div>
    <div class="dashboard-content flex flex-col gap-8 w-full max-w-7xl mx-auto px-2">
      <!-- TOP ROW: Top Accounts Snapshot & Net Income -->
      <div class="flex flex-col md:flex-row gap-6 justify-center items-stretch">
        <!-- Top Accounts Snapshot Card -->
        <div
          class="flex-1 min-w-[340px] max-w-[400px] bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-ice)] p-6 flex flex-col justify-between">
          <h2 class="text-xl font-bold mb-2 text-[var(--color-accent-ice)]">Top Accounts</h2>
          <TopAccountSnapshot />
        </div>
        <!-- Net Income Summary Card -->
        <div
          class="flex-[2_2_0%] min-w-[360px] max-w-[750px] bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-mint)] p-6 flex flex-col gap-3">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-xl font-bold text-[var(--color-accent-mint)]">Net Income (Daily)</h2>
            <ChartWidgetTopBar>
              <template #controls>
                <button
                  class="bg-[var(--color-accent-yellow)] text-[var(--color-text-dark)] px-3 py-1 rounded font-semibold transition hover:brightness-105"
                  @click="zoomedOut = !zoomedOut">
                  {{ zoomedOut ? 'Zoom In' : 'Zoom Out' }}
                </button>
              </template>
              <template #summary>
                <div>
                  Income:
                  <span class="font-bold text-[var(--color-accent-mint)]">
                    {{ formatAmount(netSummary.totalIncome) }}
                  </span>
                </div>
                <div>
                  Expenses:
                  <span class="font-bold text-red-400">
                    {{ formatAmount(netSummary.totalExpenses) }}
                  </span>
                </div>
                <div
                  class="font-bold text-lg"
                  :class="{ 'text-red-400': netSummary.totalNet < 0, 'text-[var(--color-accent-mint)]': netSummary.totalNet >= 0 }"
                >
                  Net Total: {{ formatAmount(netSummary.totalNet) }}
                </div>
              </template>
            </ChartWidgetTopBar>
          </div>
          <DailyNetChart :zoomed-out="zoomedOut" @summary-change="netSummary = $event" @bar-click="onNetBarClick" />
          <div class="mt-2 flex flex-col gap-1">
            <div>
              <span class="font-bold text-[var(--color-accent-mint)]">Income:</span>
              <span class="ml-1">{{ formatAmount(netSummary.totalIncome) }}</span>
            </div>
            <div>
              <span class="font-bold text-red-400">Expenses:</span>
              <span class="ml-1">{{ formatAmount(netSummary.totalExpenses) }}</span>
            </div>
            <div :class="netSummary.totalNet >= 0 ? 'text-[var(--color-accent-mint)]' : 'text-red-400'"
              class="font-bold">
              Net Total: {{ formatAmount(netSummary.totalNet) }}
            </div>
          </div>
        </div>
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
                  class="date-picker px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)] focus:ring-2 focus:ring-[var(--color-accent-mint)]" />
                <input type="date" v-model="catRange.end"
                  class="date-picker px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)] focus:ring-2 focus:ring-[var(--color-accent-mint)] ml-2" />
                <GroupedCategoryDropdown :groups="categoryGroups" :modelValue="catSelected"
                  @update:modelValue="onCatSelected" class="w-64" />
              </template>
              <template #summary>
                <span class="text-sm">Total:</span>
                <span class="font-bold text-lg text-[var(--color-accent-mint)]">
                  {{ formatAmount(catSummary.total) }}
                </span>
              </template>
            </ChartWidgetTopBar>
          </div>
          <CategoryBreakdownChart :start-date="catRange.start" :end-date="catRange.end"
            :selected-category-ids="catSelected" @summary-change="catSummary = $event"
            @categories-change="allCategoryIds = $event" @bar-click="onCategoryBarClick" />
          <div class="mt-1">
            <span class="font-bold">Total:</span>
            <span class="ml-1 text-[var(--color-accent-mint)] font-bold">{{ formatAmount(catSummary.total) }}</span>
          </div>
        </div>
        <!-- Spending Insights Placeholder -->
        <div
          class="flex-1 min-w-[340px] max-w-[400px] bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-blue)] p-6 flex flex-col items-center justify-center">
          <h2 class="text-xl font-bold text-[var(--color-accent-blue)] mb-4">Spending Insights</h2>
          <p class="italic text-muted text-center">More detailed insights coming soon...</p>
        </div>
      </div>

      <!-- RESERVED TABLES PANEL -->
      <div
        class="relative min-h-[440px] bg-[var(--color-bg-sec)] border-2 border-[var(--color-accent-ice)] rounded-2xl shadow-xl flex flex-col justify-center items-stretch overflow-hidden">
        <!-- Button row: Show only if neither table is expanded -->
        <div v-if="!accountsExpanded && !transactionsExpanded"
          class="flex flex-row justify-between items-center gap-8 w-full h-full p-12">
          <button @click="expandAccounts"
            class="flex-1 text-2xl font-bold px-8 py-8 rounded-2xl border-2 border-[var(--color-accent-ice)] bg-[var(--color-bg-sec)] shadow-lg hover:bg-[var(--color-accent-ice)] hover:text-[var(--color-bg-sec)] transition">
            Expand Accounts Table
          </button>
          <div class="mx-8 text-lg font-light text-muted select-none">or</div>
          <button @click="expandTransactions"
            class="flex-1 text-2xl font-bold px-8 py-8 rounded-2xl border-2 border-[var(--color-accent-yellow)] bg-[var(--color-bg-sec)] shadow-lg hover:bg-[var(--color-accent-yellow)] hover:text-[var(--color-bg-sec)] transition">
            Expand Transactions Table
          </button>
        </div>
        <!-- Expanded Accounts Table -->
        <transition name="fade">
          <div v-if="accountsExpanded" class="absolute inset-0 p-8 flex flex-col bg-[var(--color-bg-sec)]">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-2xl font-bold text-[var(--color-accent-ice)]">Accounts Table</h2>
              <button @click="collapseTables"
                class="px-4 py-2 rounded bg-[var(--color-accent-ice)] text-[var(--color-bg-sec)] font-bold text-lg shadow hover:brightness-105">
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
              <h2 class="text-2xl font-bold text-[var(--color-accent-yellow)]">Transactions Table</h2>
              <button @click="collapseTables"
                class="px-4 py-2 rounded bg-[var(--color-accent-yellow)] text-[var(--color-bg-sec)] font-bold text-lg shadow hover:brightness-105">
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

      <TransactionModal v-if="showModal" :title="modalTitle" :transactions="modalTransactions"
        @close="showModal = false" />
    </div>

    <template #footer>
      &copy; {{ new Date().getFullYear() }} braydio • pyNance.
    </template>
  </AppLayout>
</template>



<script setup>
import AppLayout from '@/components/layout/AppLayout.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import CategoryBreakdownChart from '@/components/charts/CategoryBreakdownChart.vue'
import ChartWidgetTopBar from '@/components/ui/ChartWidgetTopBar.vue'
import AccountSnapshot from '@/components/widgets/AccountSnapshot.vue'
import AccountsTable from '@/components/tables/AccountsTable.vue'
import TransactionsTable from '@/components/tables/TransactionsTable.vue'
import PaginationControls from '@/components/tables/PaginationControls.vue'
import TransactionModal from '@/components/modals/TransactionModal.vue'
import TopAccountSnapshot from '@/components/widgets/TopAccountSnapshot.vue'
import GroupedCategoryDropdown from '@/components/ui/GroupedCategoryDropdown.vue'
import { formatAmount } from '@/utils/format'
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'
import { useTransactions } from '@/composables/useTransactions.js'
import { fetchCategoryTree } from '@/api/categories'

// Transactions and user
const { searchQuery, currentPage, totalPages, filteredTransactions, sortKey, sortOrder, setSort, changePage } = useTransactions(15)
const showModal = ref(false)
const modalTransactions = ref([])
const modalTitle = ref('')
const userName = import.meta.env.VITE_USER_ID_PLAID || 'Guest'
const currentDate = new Date().toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })
const accountsCollapsed = ref(true)
const transactionsCollapsed = ref(true)
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
const netSummary = ref({ totalIncome: 0, totalExpenses: 0, totalNet: 0 })
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

// When CategoryBreakdownChart fetches, auto-select top 5 ONCE per fetch. (No repopulate on clear)
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
const atSummary = ref({ total: 0 })

// When user clears selection, do NOT re-select (unless new data is fetched)
function onCatSelected(newIds) {
  catSelected.value = Array.isArray(newIds) ? newIds : [newIds]
}

// When user changes date range, let next data load re-apply auto-select
watch(() => [catRange.value.start, catRange.value.end], () => {
  defaultSet.value = false
})

// For dropdown: fetch full tree for grouped dropdown (not just breakdown result)
const categoryGroups = ref([])
async function loadCategoryGroups() {
  try {
    const res = await fetchCategoryTree()
    if (res.status === 'success' && Array.isArray(res.data)) {
      categoryGroups.value = (res.data || []).map(root => ({
        id: root.id,
        label: root.label,
        children: (root.children || []).map(c => ({
          id: c.id,
          label: c.label ?? c.name,
        })),
      })).sort((a, b) => a.label.localeCompare(b.label))
    }
  } catch (e) {
    categoryGroups.value = []
  }
}
// For Daily Net Chart clicks
function onNetBarClick(label) {
  // label is usually a date string ("2024-07-09" etc)
  modalTransactions.value = filteredTransactions.value.filter(tx =>
    tx.date === label
  )
  modalTitle.value = `Transactions on ${label}`
  showModal.value = true
}

// For Category Chart clicks
function onCategoryBarClick(label) {
  // label is category name (may match parent or child label)
  modalTransactions.value = filteredTransactions.value.filter(tx =>
    tx.category_label === label || tx.category_parent === label
  )
  modalTitle.value = `Transactions: ${label}`
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
  @apply text-[var(--color-accent-ice)] text-lg;
  text-shadow: 2px 6px 8px var(--bar-gradient-end);
}

.text-neon-purple {
  color: var(--color-accent-ice);
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
</style>
