<template>
  <div class="container space-y-6">
    <!-- Header -->
    <header class="text-center bg-[var(--color-bg)] p-4 rounded-lg shadow-md">
      <h1>Accounts Management</h1>
      <h2></h2>
      <h3>
        Hello again
        <span class="username">{{ userName }}</span>,
        welcome back.
      </h3>
      <p>Why don't you take a seat.</p>
    </header>

    <!-- Account Actions -->
    <div class="card p-4">
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
    <div class="card p-4">
      <InstitutionTable @refresh="refreshCharts" />
    </div>


    <!-- Footer -->
    <footer class="accounts-footer">
      &copy; good dashroad.
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// ✅ NEW: State for selected Plaid products
const selectedProducts = ref([])

import LinkAccount from '@/components/forms/LinkAccount.vue'
import InstitutionTable from '@/components/tables/InstitutionTable.vue'
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue'
import AssetsBarTrended from '@/components/charts/AssetsBarTrended.vue'
import AccountsReorderChart from '@/components/charts/AccountsReorderChart.vue'
import RefreshTellerControls from '@/components/widgets/RefreshTellerControls.vue'
import RefreshPlaidControls from '@/components/widgets/RefreshPlaidControls.vue'
import TokenUpload from '@/components/forms/TokenUpload.vue'

// ✅ NEW: Import product scope selector
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
@reference "../assets/css/main.css";

.username {
  @apply text-[var(--color-accent-ice)] text-[1.2rem];
  text-shadow: 2px 6px 8px var(--bar-gradient-end);
}

.accounts-footer {
  @apply mt-12 text-center text-[0.9rem] text-[var(--color-text-muted)] border-t border-[var(--themed-border)] pt-4;
  text-shadow: 0 0 4px var(--neon-purple);
}
</style>
