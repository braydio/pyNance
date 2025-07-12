<template>
  <AppLayout>
    <!-- DASHBOARD HEADER -->
    <template #header>
      <div class="text-center space-y-1 py-4">
        <h1 class="text-4xl md:text-5xl font-extrabold tracking-wide text-neon-purple">
          Welcome, <span class="username">{{ userName }}</span>!
        </h1>
        <p class="text-sm text-muted">Today is {{ currentDate }}</p>
        <p class="italic text-muted">{{ netWorthMessage }}</p>
      </div>
    </template>

    <div class="dashboard-outer flex flex-col items-center min-h-screen w-full px-2">
      <!-- Account Snapshot -->
      <div class="w-full flex justify-center">
        <div class="max-w-3xl w-full">
          <AccountSnapshot />
        </div>
      </div>

      <!-- Chart Cards Row -->
      <div class="w-full flex justify-center my-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-5xl">
          <!-- DAILY NET INCOME CARD -->
          <div
            class="bg-[var(--color-bg-sec)] p-4 rounded-2xl shadow w-full border border-[var(--divider)] flex flex-col">
            <ChartWidgetTopBar>
              <template #icon>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-[var(--color-accent-mint)]" fill="none"
                  viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 8c-2.21 0-4-1.343-4-3s1.79-3 4-3 4 1.343 4 3c0 1.216-1.024 2.207-2.342 2.707M12 12c2.21 0 4 1.343 4 3s-1.79 3-4 3-4-1.343-4-3c0-1.216 1.024-2.207 2.342-2.707" />
                </svg>
              </template>
              <template #title>
                Daily Net Income
              </template>
              <template #controls>
                <button
                  class="bg-[var(--color-accent-yellow)] text-[var(--color-text-dark)] px-3 py-1 rounded font-semibold transition hover:brightness-105"
                  @click="zoomedOut = !zoomedOut">
                  {{ zoomedOut ? 'Zoom In' : 'Zoom Out' }}
                </button>
              </template>
              <template #summary>
                <div>Income: <span class="font-bold text-[var(--color-accent-mint)]">${{
                  netSummary.totalIncome?.toLocaleString() }}</span></div>
                <div>Expenses: <span class="font-bold text-[var(--color-accent-red)]">${{
                  netSummary.totalExpenses?.toLocaleString() }}</span></div>
                <div class="font-bold text-lg text-[var(--color-accent-mint)]">Net Total: ${{
                  netSummary.totalNet?.toLocaleString() }}</div>
              </template>
            </ChartWidgetTopBar>
            <DailyNetChart :zoomed-out="zoomedOut" @summary-change="netSummary = $event" @bar-click="onNetBarClick" />
          </div>

          <!-- SPENDING BY CATEGORY CARD -->
          <div
            class="bg-[var(--color-bg-sec)] p-4 rounded-2xl shadow w-full border border-[var(--divider)] flex flex-col">
            <ChartWidgetTopBar>
              <template #icon>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-[var(--color-accent-yellow)]" fill="none"
                  viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M3 10h4V3H3v7zm0 0v11h4v-4h6v4h4V3h-4v7H3zm7 4h2v2h-2v-2z" />
                </svg>
              </template>
              <template #title>
                Spending by Category
              </template>
              <template #controls>
                <input type="date" v-model="catRange.start"
                  class="date-picker px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)] focus:ring-2 focus:ring-[var(--color-accent-mint)]" />
                <input type="date" v-model="catRange.end"
                  class="date-picker px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)] focus:ring-2 focus:ring-[var(--color-accent-mint)]" />
                <!-- Multi-select dropdown for category parents -->
                <GroupedCategoryDropdown :groups="categoryGroups" :modelValue="catSelected"
                  @update:modelValue="onCatSelected" class="w-64" />
              </template>
              <template #summary>
                <span class="text-sm">Total:</span>
                <span class="font-bold text-lg text-[var(--color-accent-mint)]">${{ catSummary.total?.toLocaleString()
                  }}</span>
              </template>
            </ChartWidgetTopBar>
            <CategoryBreakdownChart :start-date="catRange.start" :end-date="catRange.end"
              :selected-category-ids="catSelected" @summary-change="catSummary = $event"
              @categories-change="allCategoryIds = $event" @bar-click="onCategoryBarClick" />
          </div>
        </div>
      </div>

      <!-- TABLES/OTHER WIDGETS -->
      <div class="w-full flex justify-center">
        <div class="max-w-4xl w-full">
          <BaseCard>
            <div class="space-y-4">
              <input v-model="searchQuery" type="text" placeholder="Search transactions, account, institution..."
                class="w-full p-2 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <TransactionsTable :transactions="filteredTransactions" :sort-key="sortKey" :sort-order="sortOrder"
                :search="searchQuery" @sort="setSort" :current-page="currentPage" :total-pages="totalPages"
                @change-page="changePage" />

              <PaginationControls :current-page="currentPage" :total-pages="totalPages" @change-page="changePage" />
              <AccountsTable />
            </div>
          </BaseCard>
        </div>
      </div>
      <TransactionModal v-if="showModal" :title="modalTitle" :transactions="modalTransactions"
        @close="showModal = false" />
    </div>

    <template #footer>
      &copy; {{ new Date().getFullYear() }} braydio – pyNance.
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
import GroupedCategoryDropdown from '@/components/ui/GroupedCategoryDropdown.vue'
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
const netWorth = ref(0)
const netWorthMessage = computed(() => {
  if (netWorth.value < 0) return "How terribly grim... and things are looking quite bleak."
  if (netWorth.value > 1000) return "Your fortune grows... Ahh... well in the black."
  return "Uhh... keep up the... whatever this is. How very... neutral."
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
</style>
