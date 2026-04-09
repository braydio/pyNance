<!--
  AccountsSection.vue
  Expanded accounts table container for the dashboard.
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
        <div class="dashboard-panel-kicker">Account Surfaces</div>
        <h2 class="dashboard-panel-title text-[var(--color-accent-cyan)]">Accounts Table</h2>
        <p class="dashboard-panel-copy mb-0">
          Review balances, institutions, and account health without leaving the dashboard flow.
        </p>
      </div>
      <BaseButton tone="accent" variant="outline" radius="lg" @click="emit('close')"
        >Close</BaseButton
      >
    </div>
    <div class="flex-1 min-h-[55vh] sm:min-h-[60vh] lg:min-h-[70vh]">
      <AccountsTable />
      <slot />
    </div>
  </BasePanel>
</template>

<script setup>
/**
 * Full-screen accounts table view inside the dashboard tables panel.
 */
import AccountsTable from '@/components/tables/AccountsTable.vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BasePanel from '@/components/base/BasePanel.vue'

const emit = defineEmits(['close'])
</script>
