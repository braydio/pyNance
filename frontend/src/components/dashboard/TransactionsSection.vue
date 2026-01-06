<!--
  TransactionsSection.vue
  Expanded transactions table container for the dashboard.
-->
<template>
  <div class="absolute inset-0 p-8 flex flex-col bg-[var(--color-bg-sec)]">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-bold text-[var(--color-accent-red)]">Transactions Table</h2>
      <button
        @click="emit('close')"
        class="px-4 py-2 rounded bg-[var(--color-accent-red)] text-[var(--color-bg-sec)] font-bold text-lg shadow hover:brightness-105"
      >
        Close
      </button>
    </div>
    <div class="flex-1 min-h-[50vh] sm:min-h-[60vh]">
      <TransactionsTable
        :transactions="transactions"
        :sort-key="sortKey"
        :sort-order="sortOrder"
        :search="search"
        @sort="emit('sort', $event)"
        :current-page="currentPage"
        :total-pages="totalPages"
        @change-page="emit('change-page', $event)"
      />
      <PaginationControls
        :current-page="currentPage"
        :total-pages="totalPages"
        :page-size="pageSize"
        :total-items="totalCount"
        @change-page="emit('set-page', $event)"
      />
      <slot />
    </div>
  </div>
</template>

<script setup>
/**
 * Full-screen transactions table view inside the dashboard tables panel.
 */
import TransactionsTable from '@/components/tables/TransactionsTable.vue'
import PaginationControls from '@/components/tables/PaginationControls.vue'

defineProps({
  transactions: { type: Array, default: () => [] },
  sortKey: { type: [String, null], default: null },
  sortOrder: { type: Number, default: 1 },
  search: { type: String, default: '' },
  currentPage: { type: Number, default: 1 },
  totalPages: { type: Number, default: 1 },
  pageSize: { type: Number, default: 0 },
  totalCount: { type: Number, default: 0 },
})

const emit = defineEmits(['close', 'sort', 'change-page', 'set-page'])
</script>
