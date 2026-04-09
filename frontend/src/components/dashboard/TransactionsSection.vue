<!--
  TransactionsSection.vue
  Expanded transactions table container for the dashboard.
-->
<template>
  <BasePanel
    tag="div"
    class="absolute inset-0 flex flex-col p-6 sm:p-8"
    surface="secondary"
    radius="lg"
    padding="none"
    shadow="none"
  >
    <div class="dashboard-panel-header mb-5">
      <div class="space-y-2">
        <div class="dashboard-panel-kicker">Transaction Queue</div>
        <h2 class="dashboard-panel-title text-[var(--color-accent-red)]">Transactions Table</h2>
        <p class="dashboard-panel-copy mb-0">
          Sort, search, and page through raw activity from the same dashboard drill-down surface.
        </p>
      </div>
      <BaseButton tone="danger" variant="outline" radius="lg" @click="emit('close')"
        >Close</BaseButton
      >
    </div>
    <div class="flex-1 min-h-[55vh] sm:min-h-[60vh] lg:min-h-[70vh]">
      <TransactionsTable
        :transactions="transactions"
        :sort-key="sortKey"
        :sort-order="sortOrder"
        :search="search"
        :current-page="currentPage"
        :total-pages="totalPages"
        @sort="emit('sort', $event)"
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
  </BasePanel>
</template>

<script setup>
/**
 * Full-screen transactions table view inside the dashboard tables panel.
 */
import TransactionsTable from '@/components/tables/TransactionsTable.vue'
import PaginationControls from '@/components/tables/PaginationControls.vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BasePanel from '@/components/base/BasePanel.vue'

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
