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
    </header>


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

.controls-widget {
  margin-top: 0.1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.account-controls-group {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1rem;
  background-color: var(--color-bg-secondary);
  border: 1px solid var(--color-text-muted);
  border-radius: 12px;
  padding: 1rem;
  margin-top: 0.5rem;
  box-shadow: 0px 2px 3px var(--color-accent-ice);
  width: 100%;
  max-width: 900px;
  opacity: 1;
  transition: all 0.3s ease;
}

.control-block {
  flex: 1 1 250px;
  max-width: 280px;
  background-color: var(--themed-bg);
  border: 1px solid var(--color-border-secondary);
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 6px var(--shadow);
}

.slide-vertical-enter-active,
.slide-vertical-leave-active {
  transition: all 0.3s ease;
}

.slide-vertical-enter-from,
.slide-vertical-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-10px);
  overflow: hidden;
}

.slide-vertical-enter-to,
.slide-vertical-leave-from {
  max-height: 500px;
  opacity: 1;
  transform: translateY(0);
}


.accounts-header {
  text-align: center;
  background-color: var(--color-bg);
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px var(--shadow);
}

.accounts-header h1 {
  color: var(--color-accent-);
  margin: 0;
  font-size: 2rem;
  text-shadow: 0px 0px 8px var(--color-accent-yellow);
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
}
</style>
