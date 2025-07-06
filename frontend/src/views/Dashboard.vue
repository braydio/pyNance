<template>
  <AppLayout>
    <!-- Header -->
    <template #header>
      <div class="text-center space-y-1 py-4">
        <h1 class="text-4xl md:text-5xl font-extrabold tracking-wide text-neon-purple">
          Welcome, <span class="username">{{ userName }}</span>!
        </h1>
        <p class="text-sm text-muted">Today is {{ currentDate }}</p>
        <p class="italic text-muted">{{ netWorthMessage }}</p>
      </div>
    </template>

    <!-- Account snapshot / summary -->
    <div class="space-y-8">
      <AccountSnapshot />

      <!-- Unified grid for main charts -->
      <div class="grid md:grid-cols-2 gap-8">
        <!-- Net Income Chart Card -->
        <div class="bg-[var(--color-bg-sec)] p-4 rounded-2xl shadow w-full border border-[var(--divider)]">
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
              <!-- Controls are inside the chart component -->
            </template>
            <template #summary>
              <!-- Summary from chart -->
            </template>
          </ChartWidgetTopBar>
          <DailyNetChart />
        </div>

        <!-- Category Breakdown Chart Card -->
        <div class="bg-[var(--color-bg-sec)] p-4 rounded-2xl shadow w-full border border-[var(--divider)]">
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
              <!-- Controls are inside the chart component -->
            </template>
            <template #summary>
              <!-- Summary from chart -->
            </template>
          </ChartWidgetTopBar>
          <CategoryBreakdownChart />
        </div>
      </div>

      <!-- Table and snapshot area -->
      <BaseCard>
        <div class="space-y-4">
          <input v-model="searchQuery" type="text" placeholder="Search transactions..."
            class="w-full p-2 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <TransactionsTable :transactions="filteredTransactions" :sort-key="sortKey" :sort-order="sortOrder"
            @sort="setSort" />
          <PaginationControls :current-page="currentPage" :total-pages="totalPages" @change="changePage" />
          <AccountsTable />
        </div>
      </BaseCard>
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

import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import { fetchTransactions as fetchTransactionsApi } from '@/api/transactions'
import { useTransactions } from '@/composables/useTransactions.js'

const { searchQuery, currentPage, totalPages, filteredTransactions, sortKey, sortOrder, setSort, changePage } = useTransactions(15)
const showModal = ref(false)
const modalTransactions = ref([])
const modalTitle = ref('')

const userName = import.meta.env.VITE_USER_ID_PLAID || 'Guest'
const currentDate = new Date().toLocaleDateString(undefined, {
  month: 'long',
  day: 'numeric',
  year: 'numeric',
})

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
  } catch (e) {
    console.error('Failed to fetch net assets:', e)
  }
})
</script>

<style scoped>
@import "../assets/css/main.css";

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
