<!--
  AccountsSection.vue
  Expanded accounts table container for the dashboard.
-->
<template>
  <div class="absolute inset-0 p-6 sm:p-8 flex flex-col bg-[var(--color-bg-sec)]">
    <div class="dashboard-panel-header mb-5">
      <div class="space-y-2">
        <div class="dashboard-panel-kicker">Account Surfaces</div>
        <h2 class="dashboard-panel-title text-[var(--color-accent-cyan)]">Accounts Table</h2>
        <p class="dashboard-panel-copy mb-0">
          Review balances, institutions, and account health without leaving the dashboard flow.
        </p>
      </div>
      <button
        class="btn btn-outline rounded-xl border-[var(--color-accent-cyan)] text-[var(--color-accent-cyan)] hover:bg-[var(--color-accent-cyan)] hover:text-[var(--color-bg-dark)]"
        @click="emit('close')"
      >
        Close
      </button>
    </div>
    <div class="flex-1 min-h-[55vh] sm:min-h-[60vh] lg:min-h-[70vh]">
      <AccountsTable />
      <slot />
    </div>
  </div>
</template>

<script setup>
/**
 * Full-screen accounts table view inside the dashboard tables panel.
 */
import AccountsTable from '@/components/tables/AccountsTable.vue'

const emit = defineEmits(['close'])
</script>
