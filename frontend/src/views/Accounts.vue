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
    <section class="p-6 bg-[var(--color-bg-secondary)] rounded-lg shadow-lg border border-[var(--divider)]">
      <div class="flex flex-wrap gap-4 justify-center">
        <LinkAccount :selected-products="selectedProducts" @manual-token-click="toggleManualTokenMode" />

        <button @click="togglePlaidRefresh"
          class="px-4 py-2 rounded bg-[var(--color-accent-blue)] text-white font-semibold shadow hover:bg-opacity-80 transition">
          {{ showPlaidRefresh ? 'Hide' : 'Refresh' }} Plaid Accounts
        </button>
        <Transition name="fade-slide" mode="out-in">
          <div v-if="showPlaidRefresh" class="w-full">
            <RefreshPlaidControls />
          </div>
        </Transition>

        <button @click="toggleTellerRefresh"
          class="px-4 py-2 rounded bg-[var(--color-accent-mint)] text-black font-semibold shadow hover:bg-opacity-80 transition">
          {{ showTellerRefresh ? 'Hide' : 'Refresh' }} Teller Accounts
        </button>
        <Transition name="fade-slide" mode="out-in">
          <div v-if="showTellerRefresh" class="w-full">
            <RefreshTellerControls />
          </div>
        </Transition>

        <TokenUpload v-if="showTokenForm" @cancel="toggleManualTokenMode" />
      </div>
    </section>

    <!-- Net Change Summary -->
    <section class="p-4 bg-[var(--color-bg-secondary)] rounded-lg shadow-md space-y-2">
      <h2 class="font-bold text-lg">Net Change Summary</h2>
      <p v-if="summaryError" class="text-red-500">{{ summaryError }}</p>
      <p v-else-if="loadingSummary">Loading...</p>
      <div v-else class="flex gap-6">
        <div>Income: {{ formatCurrency(netSummary.income) }}</div>
        <div>Expense: {{ formatCurrency(netSummary.expense) }}</div>
        <div>Net: {{ formatCurrency(netSummary.net) }}</div>
      </div>
    </section>

    <!-- Recent Transactions -->
    <section class="p-4 bg-[var(--color-bg-secondary)] rounded-lg shadow-md space-y-2">
      <h2 class="font-bold text-lg">Recent Transactions</h2>
      <p v-if="transactionsError" class="text-red-500">{{ transactionsError }}</p>
      <p v-else-if="loadingTransactions">Loading...</p>
      <TransactionsTable v-else :transactions="recentTransactions" />
    </section>

    <!-- Charts -->
    <section class="flex flex-col gap-6">
      <div class="flex flex-wrap gap-2 justify-between items-start">
        <div
          class="flex-1 shrink basis-[48%] max-w-[48%] min-w-[300px] p-4 bg-[var(--color-bg-secondary)] rounded-lg shadow-md">
          <NetYearComparisonChart />
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
    <footer
      class="mt-12 text-center text-sm text-[var(--color-text-muted)] border-t border-[var(--themed-border)] pt-4">
      &copy; good dashroad.
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import TransactionsTable from '@/components/tables/TransactionsTable.vue'
import { fetchNetChanges, fetchRecentTransactions } from '@/api/accounts'

// State
const selectedProducts = ref([])
const showTokenForm = ref(false)
const showPlaidRefresh = ref(false)
const showTellerRefresh = ref(false)
const reorderChart = ref(null)

const loadingSummary = ref(false)
const loadingTransactions = ref(false)
const summaryError = ref('')
const transactionsError = ref('')
const netSummary = ref({ income: 0, expense: 0, net: 0 })
const recentTransactions = ref([])
const selectedAccountId = ref(null)

// Environment
const userName = import.meta.env.VITE_USER_ID_PLAID || 'Guest'

// Methods
function toggleManualTokenMode() {
  showTokenForm.value = !showTokenForm.value
}

function togglePlaidRefresh() {
  showPlaidRefresh.value = !showPlaidRefresh.value
}

function toggleTellerRefresh() {
  showTellerRefresh.value = !showTellerRefresh.value
}

function refreshCharts() {
  reorderChart.value?.refresh?.()
}

function formatCurrency(val) {
  const num = parseFloat(val || 0)
  return num.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

async function loadSummary(accountId) {
  loadingSummary.value = true
  summaryError.value = ''
  try {
    const res = await fetchNetChanges(accountId)
    if (res.status === 'success') {
      netSummary.value = {
        income: res.data.income || 0,
        expense: res.data.expense || 0,
        net: res.data.net || 0,
      }
    } else {
      summaryError.value = res.message || 'Error loading summary'
    }
  } catch (err) {
    summaryError.value = err.message || 'Error loading summary'
  } finally {
    loadingSummary.value = false
  }
}

async function loadTransactions(accountId) {
  loadingTransactions.value = true
  transactionsError.value = ''
  try {
    const res = await fetchRecentTransactions(accountId, 10)
    if (res.status === 'success') {
      recentTransactions.value = res.data.transactions || []
    } else {
      transactionsError.value = res.message || 'Error loading transactions'
    }
  } catch (err) {
    transactionsError.value = err.message || 'Error loading transactions'
  } finally {
    loadingTransactions.value = false
  }
}

onMounted(async () => {
  try {
    const res = await api.getAccounts()
    if (res.status === 'success' && res.accounts.length) {
      selectedAccountId.value = res.accounts[0].account_id
      await Promise.all([
        loadSummary(selectedAccountId.value),
        loadTransactions(selectedAccountId.value),
      ])
    }
  } catch (err) {
    summaryError.value = 'Failed to load account list'
  }
})

// Components
import LinkAccount from '@/components/forms/LinkAccount.vue'
import InstitutionTable from '@/components/tables/InstitutionTable.vue'
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue'
import AssetsBarTrended from '@/components/charts/AssetsBarTrended.vue'
import AccountsReorderChart from '@/components/charts/AccountsReorderChart.vue'
import RefreshTellerControls from '@/components/widgets/RefreshTellerControls.vue'
import RefreshPlaidControls from '@/components/widgets/RefreshPlaidControls.vue'
import TokenUpload from '@/components/forms/TokenUpload.vue'
</script>

<style scoped>
@reference "../assets/css/main.css";
.username {
  @apply text-[var(--color-accent-ice)] text-lg;
  text-shadow: 2px 6px 8px var(--bar-gradient-end);
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}

.fade-slide-enter-to {
  opacity: 1;
  transform: translateY(0);
}

.fade-slide-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
