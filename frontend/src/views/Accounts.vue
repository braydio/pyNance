<template>
  <div class="accounts-view">
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
    <div class="card section-container controls-section">
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
    <div class="card section-container">
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
.chart-controls-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: space-between;
  align-items: flex-start;
}

.controls-panel {
  flex: 1 1 48%;
  max-width: 48%;
  min-width: 300px;
  background-color: var(--color-bg-secondary);
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow);
  padding: 0.75rem;
}

@media (max-width: 768px) {
  .chart-controls-row {
    flex-direction: column;
  }

  .controls-panel {
    max-width: 100%;
    flex-basis: 100%;
  }
}

.controls-widget {
  margin-top: 0.1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Controls Section Styles */
.controls-section .controls-group {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
}

.accounts-header {
  text-align: center;
  background-color: var(--color-bg);
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px var(--shadow);
}

.accounts-header h1 {
  color: var(--accent-yellow-soft);
  margin: 0;
  font-size: 2rem;
  text-shadow: 0px 0px 8px var(--accent-yellow-soft);
}

.accounts-header h2 {
  color: var(--color-accent-yellow);
  margin: 2px;
  font-style: italic;
  font-size: 1.5rem;
  text-shadow: 2px 0px 6px var(--color-accent-yellow);
}

.accounts-header h3 {
  color: var(--neon-mint);
  margin: 0;
  font-style: bold;
  font-size: 1rem;
  text-shadow: 0px 1px 6px var(--color-accent-yellow);
}

.username {
  color: var(--color-accent-ice);
  margin: 0;
  font-size: 1.2rem;
  text-shadow: 2px 6px 8px var(--bar-gradient-end);
}

.accounts-header p {
  color: var(--color-accent-magenta);
  margin: 0;
  font-style: italic;
  font-size: 0.9rem;
  text-shadow: 2px 4px 6px var(--bar-gradient-end);
}

.charts-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.chart-container,
.section-container {
  padding: 1rem;
  background-color: var(--color-bg-secondary);
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow);
}

.account-tabs {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.account-tabs button {
  border: 1px solid var(--divider);
}

.account-tabs .active-tab {
  background-color: var(--color-accent-mint);
  color: var(--color-bg-dark);
  box-shadow: 0 0 6px var(--neon-mint);
}

.accounts-footer {
  margin-top: 3rem;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  border-top: 1px solid var(--themed-border);
  padding-top: 1rem;
  text-shadow: 0 0 4px var(--neon-purple);
}
</style>
