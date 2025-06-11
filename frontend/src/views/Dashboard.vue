<template>
  <AppLayout>
    <template #header>
      <h1 class="text-3xl font-bold text-blue-600">Hello {{ userName }}</h1>
      <h2 class="mt-1 text-gray-600">Today is {{ currentDate }}</h2>
      <h2 class="mt-1 text-gray-600 italic">and things are looking quite bleak.</h2>
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
      <TransactionModal v-if="showModal" :title="modalTitle" :transactions="modalTransactions" @close="showModal = false" />
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
import { ref } from 'vue'

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

const userName = import.meta.env.VITE_USER_ID_PLAID || 'Guest'
const currentDate = new Date().toLocaleDateString(undefined, {
  month: 'long',
  day: 'numeric',
  year: 'numeric',
})
</script>
