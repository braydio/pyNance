<template>
  <AppLayout>
    <template #header>
      <div class="text-center space-y-1 py-4">
        <h1 class="text-4xl md:text-5xl font-extrabold tracking-wide text-neon-purple">
          Hello <span class="username">{{ userName }}</span>,
        </h1>
        <p class="text-sm text-muted">Today is {{ currentDate }}</p>
        <p class="italic text-muted">{{ netWorthMessage }}</p>
        <!-- Expandable Toggle Button -->
        <button
          class="mt-4 px-4 py-2 bg-accent-mint/90 hover:bg-accent-mint transition rounded-xl shadow text-gray-900 flex items-center mx-auto"
          @click="showSnapshot = !showSnapshot" aria-expanded="showSnapshot">
          <i :class="showSnapshot ? 'i-carbon-chevron-up' : 'i-carbon-chevron-down'" class="mr-2"></i>
          {{ showSnapshot ? 'Hide Accounts Snapshot' : 'Show Accounts Snapshot' }}
        </button>
      </div>
      <!-- Animated Expandable Section -->
      <Transition name="fade-slide">
        <div v-if="showSnapshot" class="flex justify-center pt-6">
          <BaseCard class="w-full max-w-xl">
            <AccountSnapshot />
          </BaseCard>
        </div>
      </Transition>
    </template>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch py-2">
      <!-- Daily Net Trend Chart -->
      <div class="flex flex-col">
        <BaseCard class="h-full flex flex-col">
          <DailyNetChart @bar-click="openDayModal" />
        </BaseCard>
      </div>
      <!-- Category Breakdown Chart -->
      <div class="flex flex-col">
        <BaseCard class="h-full flex flex-col">
          <CategoryBreakdownChart :limit="5" stacked @bar-click="openCategoryModal" />
        </BaseCard>
      </div>
    </div>

    <div class="mt-8">
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
      &copy; good dashboard.
    </template>
  </AppLayout>
</template>

<script setup>
import AppLayout from '@/components/layout/AppLayout.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import PaginationControls from '@/components/tables/PaginationControls.vue'
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

const showSnapshot = ref(false)

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

const NEGATIVE_MESSAGES = [
  "The absolute state...",
  "Isn't this all rather terribly grim...",
  "This... this is not good.",
  'Things are looking quite bleak.',
  "To shreds you say?",
]
const POSITIVE_MESSAGES = [
  'Your fortune grows...',
  "Your affairs are in a most enviable state!",
  "A marvelous testament to your financial acumen!",
  "Financial sophistication at its finest.",
  "Ah... well in the black."
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
.username {
  @apply text-[var(--color-accent-ice)] text-lg;
  text-shadow: 2px 6px 8px var(--bar-gradient-end);
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-16px) scale(0.98);
}
</style>
