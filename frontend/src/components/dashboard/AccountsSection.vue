<!--
  AccountsSection.vue
  Expanded accounts table container for the dashboard.
-->
<template>
  <div class="absolute inset-0 p-8 flex flex-col bg-[var(--color-bg-sec)]">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-bold text-[var(--color-accent-cyan)]">Accounts Table</h2>
      <button
        @click="emit('close')"
        class="px-4 py-2 rounded bg-[var(--color-accent-cyan)] text-[var(--color-bg-sec)] font-bold text-lg shadow hover:brightness-105"
      >
        Close
      </button>
    </div>
    <div class="flex-1 min-h-[50vh] sm:min-h-[60vh]">
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
