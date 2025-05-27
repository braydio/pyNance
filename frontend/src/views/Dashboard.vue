<template>
  <AppLayout>
    <template #header>
      <h1 class="text-3xl font-bold text-blue-600">Hello {{ userName }}</h1>
      <h2 class="mt-1 text-gray-600">Today is {{ currentDate }}</h2>
      <h2 class="mt-1 text-gray-600 italic">and things are looking quite bleak.</h2>
    </template>

    <div class="space-y-8">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <BaseCard>
          <DailyNetChart />
        </BaseCard>
        <BaseCard>
          <CategoryBreakdownChart />
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

const userName = import.meta.env.VITE_USER_ID_PLAID || 'Guest'
const currentDate = new Date().toLocaleDateString(undefined, {
  month: 'long',
  day: 'numeric',
  year: 'numeric',
})
</script>
