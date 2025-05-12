<template>
  <div class="accounts-view">
    <!-- Header -->

    <header class="accounts-header">
      <h1>Accounts Management</h1>
      <h2></h2>
      <h3>
        Hello again
        <span class="username">{{ userName }}</span>,
        welcome back.
      </h3>
      <p>Why don't you come have a seat.</p>
    </header>
    <!-- Charts -->

  <div class="chart-row-3col">
    <div class="chart-container">
      <NetYearComparisonChart />
    </div>

    <div class="controls-panel">
      <h4 class="panel-title">Account Controls</h4>
      <div class="controls-widget">
        <button class="btn btn-pill btn-outline" @click="toggleControls">
          {{ showControls ? 'Hide Controls' : 'Link / Refresh' }}
        </button>

        <transition name="slide-vertical" mode="out-in">
          <div v-if="showControls" class="account-controls-group">
            <template v-if="!showTokenForm">
              <LinkAccount @manual-token-click="toggleManualTokenMode" />
              <RefreshPlaidControls />
              <RefreshTellerControls />
            </template>
            <TokenUpload v-else @cancel="toggleManualTokenMode" />
          </div>
        </transition>
      </div>
    </div>

    <div class="chart-container">
      <AssetsBarTrended />
    </div>
  </div>

  <div class="chart-container">
    <AccountsReorderChart />
  </div>


    <transition name="slide-horizontal" mode="out-in">
      <div class="card section-container" :key="activeAccountGroup">
        <AccountsTable :accountGroup="activeAccountGroup" />
      </div>
    </transition>

    <!-- Account Tabs -->
    <section class="section-container">
      <div class="account-tabs">
        <button v-for="group in accountGroups" :key="group" class="btn btn-pill"
          :class="{ 'active-tab': activeAccountGroup === group }" @click="activeAccountGroup = group">
          {{ group }}
        </button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="accounts-footer">
      &copy; good dashroad.
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import LinkAccount from '@/components/LinkAccount.vue'
import AccountsTable from '@/components/AccountsTable.vue'
import NetYearComparisonChart from '@/components/NetYearComparisonChart.vue'
import AssetsBarTrended from '@/components/AssetsBarTrended.vue'
import AccountsReorderChart from '@/components/AccountsReorderChart.vue'
import RefreshTellerControls from '@/components/RefreshTellerControls.vue'
import RefreshPlaidControls from '@/components/RefreshPlaidControls.vue'
import TokenUpload from '@/components/TokenUpload.vue'

const userName = import.meta.env.VITE_USER_ID_PLAID || ''
const currentDate = new Date().toLocaleDateString(undefined, {
  month: 'long',
  day: 'numeric',
  year: 'numeric'
})

const activeAccountGroup = ref('Checking')
const accountGroups = ['Checking', 'Savings', 'Credit']
const showControls = ref(false)
const showTokenForm = ref(false)

function toggleControls() {
  showControls.value = !showControls.value
}

function toggleManualTokenMode() {
  showTokenForm.value = !showTokenForm.value
}
</script>

<style scoped>
.chart-row-3col {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  gap: .5rem;
  flex-wrap: wrap;
}

.chart-row-3col > .chart-container {
  flex: 1 1 38%;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.controls-panel {
  flex: 1 1 24%;
  min-width: 300px;
  max-width: 200px;
  background-color: var(--color-bg-secondary);
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--neon-mint-soft);
  padding: 1.2rem;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: stretch;
}

.panel-title {
  font-size: 1rem;
  text-align: center;
  color: var(--color-accent-yellow);
  margin-bottom: 0.75rem;
}

.controls-widget {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.controls-widget > button {
  align-self: center;
}

.account-controls-group {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--color-text-muted);
  border-radius: 10px;
  background-color: var(--color-bg);
  box-shadow: 0 1px 4px var(--color-accent-ice);
}

/* Responsive */
@media (max-width: 900px) {
  .chart-row-3col {
    flex-direction: column;
    align-items: stretch;
  }

  .chart-row-3col > .chart-container,
  .controls-panel {
    max-width: 100%;
  }
}
</style>
