<template>
  <div class="accounts-view">
    <!-- Header -->
    <header class="accounts-header">
      <h1>Accounts Management</h1>
      <h2>Now with Accounts!</h2>
      <p>
      Hello again, {{ userName }}
      </p>
      <p>It is still {{ currentDate }}.</p>
    </header>

    <!-- Control Buttons -->
    <section class="controls-widget">
      <button class="btn btn-pill" @click="toggleControls">Controls</button>
      <transition name="slide-horizontal" mode="out-in">
        <div v-if="showControls" class="controls-container">
          <transition name="slide-horizontal" mode="out-in">
            <template v-if="!showTokenForm">
              <div class="controls-buttons">
                <LinkAccount class="btn btn-outline btn-pill" @manual-token-click="toggleManualTokenMode" />
                <RefreshPlaidControls class="btn btn-outline btn-pill" />
                <RefreshTellerControls class="btn btn-outline btn-pill" />
              </div>
            </template>
            <template v-else>
              <TokenUpload @cancel="toggleManualTokenMode" />
            </template>
          </transition>
        </div>
      </transition>
    </section>

    <!-- Charts -->
    <section class="charts-section">
      <div class="chart-container">
        <NetYearComparisonChart />
      </div>
      <div class="chart-container">
        <AssetsBarTrended />
      </div>
      <div class="chart-container">
        <AccountsReorderChart />
      </div>
    </section>

    <!-- Accounts Table -->
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
const showControls = ref(true)
const showTokenForm = ref(false)

function toggleControls() {
  showControls.value = !showControls.value
}

function toggleManualTokenMode() {
  showTokenForm.value = !showTokenForm.value
}
</script>

<style scoped>
.accounts-view {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--page-bg);
  color: var(--color-text-light);
  padding: 1.5rem;
  gap: 1.5rem;
}

.accounts-header {
  text-align: center;
  background-color: var(--color-bg-secondary);
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px var(--shadow);
}

.accounts-header h1 {
  color: var(--color-accent-yellow);
  margin: 0;
  font-size: 2rem;
  text-shadow: 0 0 6px var(--color-accent-yellow);
}

.controls-widget {
  position: relative;
}

.controls-container {
  margin-top: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
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
}
</style>
