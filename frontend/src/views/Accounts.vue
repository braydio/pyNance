<template>
  <div class="container space-y-8">
    <!-- Header -->
    <header class="text-center bg-[var(--color-bg)] p-4 rounded-lg shadow-md space-y-1">
      <h1 class="text-[var(--accent-yellow-soft)] text-2xl font-bold">Accounts Management</h1>
      <h2 class="text-[var(--color-accent-yellow)] italic text-xl"></h2>
      <h3 class="text-[var(--neon-mint)] font-bold">
        Hello again
        <span class="username">{{ userName }}</span>,
        welcome back.
      </h3>
      <p class="text-[var(--color-accent-magenta)] italic text-sm">Why don't you take a seat.</p>
    </header>

    <!-- Account Actions -->
    <div class="p-6 bg-[var(--color-bg-secondary)] rounded-lg shadow-lg border border-[var(--divider)]">
      <div class="flex flex-wrap gap-4 justify-center">
        <LinkAccount :selected-products="selectedProducts" @manual-token-click="toggleManualTokenMode" />
        <RefreshPlaidControls />
        <RefreshTellerControls />
        <TokenUpload v-if="showTokenForm" @cancel="toggleManualTokenMode" />
      </div>
    </div>

    <!-- Charts -->
    <section class="flex flex-col gap-6">
      <div class="flex flex-wrap gap-2 justify-between items-start">
        <div class="flex-1 shrink basis-[48%] max-w-[48%] min-w-[300px] p-4 bg-[var(--color-bg-secondary)] rounded-lg shadow-md">
          <NetYearComparisonChart />
        </div>
        <div class="flex-1 shrink basis-[48%] max-w-[48%] min-w-[300px] bg-[var(--color-bg-secondary)] rounded-lg shadow-md p-3">
          <PlaidProductScopeSelector v-model="selectedProducts" />
        </div>
      </div>

      <div class="p-4 bg-[var(--color-bg-secondary)] rounded-lg shadow-md">
        <AssetsBarTrended />
      </div>
      <div class="p-4 bg-[var(--color-bg-secondary)] rounded-lg shadow-md">
        <AccountsReorderChart ref="reorderChart" />
      </div>
    </section>

    <!-- Accounts Table -->
    <div class="p-6 bg-[var(--color-bg-secondary)] rounded-lg shadow-lg border border-[var(--divider)]">
     <InstitutionTable @refresh="refreshCharts" />
    </div>


    <!-- Footer -->
    <footer class="mt-12 text-center text-sm text-[var(--color-text-muted)] border-t border-[var(--themed-border)] pt-4">
      &copy; good dashroad.
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const selectedProducts = ref([])

import LinkAccount from '@/components/forms/LinkAccount.vue'
import InstitutionTable from '@/components/tables/InstitutionTable.vue'
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue'
import AssetsBarTrended from '@/components/charts/AssetsBarTrended.vue'
import AccountsReorderChart from '@/components/charts/AccountsReorderChart.vue'
import RefreshTellerControls from '@/components/widgets/RefreshTellerControls.vue'
import RefreshPlaidControls from '@/components/widgets/RefreshPlaidControls.vue'
import TokenUpload from '@/components/forms/TokenUpload.vue'

import PlaidProductScopeSelector from '@/components/forms//PlaidProductScopeSelector.vue'

const reorderChart = ref(null)
function refreshCharts() {
  reorderChart.value?.refresh()
}

// Meta & State
const userName = import.meta.env.VITE_USER_ID_PLAID || ''

const showTokenForm = ref(false)

function toggleManualTokenMode() {
  showTokenForm.value = !showTokenForm.value
}
</script>

<style scoped>
.username {
  @apply text-[var(--color-accent-ice)] text-lg;
  text-shadow: 2px 6px 8px var(--bar-gradient-end);
}
</style>
