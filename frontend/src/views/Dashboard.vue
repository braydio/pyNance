<!-- Dashboard view: main user landing page displaying finance overview -->
<template>
  <AppLayout>
    <template #header>
      <div class="text-center space-y-1 py-4">
        <h1 class="text-4xl md:text-5xl font-extrabold tracking-wide text-neon-purple">
          Hello
          <span class="username">{{ userName }}</span>,
        </h1>
        <p class="text-sm text-muted">Today is {{ currentDate }}</p>
        <p class="italic text-muted">{{ netWorthMessage }}</p>
      </div>
    </template>

    <div class="space-y-8">
      <AccountSnapshot />
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <BaseCard>
          <DailyNetChart @bar-click="openDayModal" />
        </BaseCard>
        <BaseCard>
          <CategoryBreakdownChart @bar-click="openCategoryModal" />
        </BaseCard>
      </div>

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
      &copy; good dashroad.
    </template>
  </AppLayout>
</template>

<script setup>
import AppLayout from '@/components/layout/AppLayout.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import PaginationControls from '@/components/tables//PaginationControls.vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import CategoryBreakdownChart from '@/components/charts/CategoryBreakdownChart.vue'
import AccountsTable from '@/components/tables/AccountsTable.vue'
import TransactionsTable from '@/components/tables/TransactionsTable.vue'
import TransactionModal from '@/components/modals/TransactionModal.vue'
import AccountSnapshot from '@/components/widgets/AccountSnapshot.vue'
import axios from 'axios'
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'

import { useTransactions } from '@/composables/useTransactions.js'

const {
  searchQuery,
  currentPage,
  totalPages,
  filteredTransactions,
  changePage,
  sortKey,
  sortOrder,
  setSort,
} = useTransactions(15)

const showModal = ref(false)
const modalTransactions = ref([])
const modalTitle = ref('')
const netWorth = ref(0)

async function openDayModal(date) {
  modalTitle.value = `Transactions for ${date}`
  const res = await axios.get('/api/transactions/get_transactions', {
    params: { start_date: date, end_date: date, page_size: 100 }
  })
  if (res.data.status === 'success') {
    modalTransactions.value = res.data.data.transactions
  } else {
    modalTransactions.value = []
  }
  showModal.value = true
}

async function openCategoryModal(category) {
  modalTitle.value = `Transactions for ${category}`
  const res = await axios.get('/api/transactions/get_transactions', {
    params: { category, page_size: 100 }
  })
  if (res.data.status === 'success') {
    modalTransactions.value = res.data.data.transactions
  } else {
    modalTransactions.value = []
  }
  showModal.value = true
}

/**
 * Display a context-aware greeting based on the latest net worth value.
 * Negative balances pull from `NEGATIVE_MESSAGES`, values above $1000 from
 * `POSITIVE_MESSAGES`, and everything else from `NEUTRAL_MESSAGES`.
 */
const NEGATIVE_MESSAGES = [
  "The absolute state...",
  'How terribly grim...',
  "This... this is not good.",
  'Things are looking quite bleak.',
  "To shreds you say?",
]
const POSITIVE_MESSAGES = [
  'Your fortune grows...',
  "Your affairs are in a most enviable state!",
  "A marvelous testament to your financial acumen!",
  "Financial sophistication at its finest.",
  "Ahh... well in the black."
]
const NEUTRAL_MESSAGES = ["Oh, yes it's you... well, keep up the... whatever this is.", "Hmm... hm? ...hmmm..."]


const netWorthMessage = computed(() => {
  const worth = Number(netWorth.value || 0)
  if (worth < 0) {
    return NEGATIVE_MESSAGES[Math.floor(Math.random() * NEGATIVE_MESSAGES.length)]
  }
  if (worth > 1000) {
    return POSITIVE_MESSAGES[Math.floor(Math.random() * POSITIVE_MESSAGES.length)]
  }
  return NEUTRAL_MESSAGES[Math.floor(Math.random() * NEUTRAL_MESSAGES.length)]
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

const userName = import.meta.env.VITE_USER_ID_PLAID || 'Guest'
const currentDate = new Date().toLocaleDateString(undefined, {
  month: 'long',
  day: 'numeric',
  year: 'numeric',
})
</script>

<style scoped>
@reference "../assets/css/main.css";

.username {
  @apply text-[var(--color-accent-ice)] text-lg;
  text-shadow: 2px 6px 8px var(--bar-gradient-end);
}
</style>
