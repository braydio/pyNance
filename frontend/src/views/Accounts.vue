<template>
  <div class="accounts-page container space-y-8">
    <!-- Header -->
    <Card class="p-6 flex items-center gap-3">
      <Wallet class="w-6 h-6" />
      <div>
        <h1 class="text-2xl font-bold">Accounts</h1>
        <p class="text-muted">Link and refresh your accounts</p>
      </div>
    </Card>

    <!-- Account Actions -->
    <Card class="p-6">
      <h2 class="text-xl font-semibold mb-4">Account Actions</h2>
      <div class="flex flex-wrap gap-4 justify-start">
        <LinkAccount :selected-products="selectedProducts" @manual-token-click="toggleManualTokenMode" />
        
        <UiButton variant="primary" @click="navigateToPlanning">
          Plan Account
        </UiButton>
        
        <TokenUpload v-if="showTokenForm" @cancel="toggleManualTokenMode" class="w-full mt-4" />
      </div>
      
      <div class="mt-6 space-y-4">
        <TogglePanel v-model="showPlaidRefresh" title="Refresh Plaid Accounts">
          <RefreshPlaidControls />
        </TogglePanel>
        
        <TogglePanel v-model="showTellerRefresh" title="Refresh Teller Accounts">
          <RefreshTellerControls />
        </TogglePanel>
      </div>
    </Card>

    <!-- Net Change Summary -->
    <Card class="p-6">
      <h2 class="text-xl font-semibold mb-4">Net Change Summary</h2>
      <div v-if="loadingSummary" class="text-center py-4 text-muted">Loading summary...</div>
      <div v-else-if="summaryError" class="text-center py-4 text-error">Failed to load summary</div>
      <div v-else class="flex justify-around">
        <div>Income: <span class="font-bold text-accent-green">{{ formatAmount(netSummary.income) }}</span></div>
        <div>Expense: <span class="font-bold text-accent-red">{{ formatAmount(netSummary.expense) }}</span></div>
        <div>Net: <span class="font-bold text-accent-yellow">{{ formatAmount(netSummary.net) }}</span></div>
      </div>
    </Card>

    <!-- Balance History -->
    <Card class="p-6 space-y-4">
      <div class="flex justify-between items-center">
        <h2 class="text-xl font-semibold">Balance History</h2>
        <select v-model="selectedRange" data-testid="filter-dropdown" class="border rounded p-1">
          <option value="7d">7d</option>
          <option value="30d">30d</option>
          <option value="90d">90d</option>
          <option value="365d">365d</option>
        </select>
      </div>
      <div v-if="loadingHistory" class="text-center py-4 text-muted">Loading...</div>
      <div v-else-if="historyError" class="text-center py-4 text-error">Failed to load history</div>
      <AccountBalanceHistoryChart v-else :balances="accountHistory" data-testid="history-chart" />
    </Card>

    <!-- Recent Transactions -->
    <Card class="p-6 space-y-4">
      <h2 class="text-xl font-semibold">Recent Transactions</h2>
      <div v-if="loadingTransactions" class="text-center py-4 text-muted">Loading...</div>
      <div v-else-if="transactionsError" class="text-center py-4 text-error">Failed to load transactions</div>
      <TransactionsTable v-else :transactions="recentTransactions" />
    </Card>

    <!-- Charts -->
    <section class="space-y-4">
      <h2 class="text-xl font-semibold">Account Analysis</h2>
      <div class="flex flex-col gap-6">
        <Card class="p-6">
          <h3 class="text-lg font-medium mb-4">Year Comparison</h3>
          <NetYearComparisonChart />
        </Card>
        <Card class="p-6">
          <h3 class="text-lg font-medium mb-4">Assets Trend</h3>
          <AssetsBarTrended />
        </Card>
        <Card class="p-6">
          <h3 class="text-lg font-medium mb-4">Account Balance Distribution</h3>
          <AccountsReorderChart ref="reorderChart" />
        </Card>
      </div>
    </section>

    <!-- Accounts Table -->
    <Card class="p-6">
      <h2 class="text-xl font-semibold mb-4">Institutions</h2>
      <InstitutionTable @refresh="refreshCharts" />
    </Card>

    <!-- Footer -->
    <footer class="mt-12 text-center text-sm text-muted border-t pt-4">
      &copy; good dashroad.
    </footer>
  </div>
</template>

<script setup>
// Dependencies and 3rd party
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Wallet } from 'lucide-vue-next'

// API and utilities
import { fetchNetChanges, fetchRecentTransactions, fetchAccountHistory } from '@/api/accounts'
import { formatAmount } from '@/utils/format'

// UI Components
import UiButton from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import TogglePanel from '@/components/ui/TogglePanel.vue'

// Business Components
import LinkAccount from '@/components/forms/LinkAccount.vue'
import InstitutionTable from '@/components/tables/InstitutionTable.vue'
import TokenUpload from '@/components/forms/TokenUpload.vue'
import TransactionsTable from '@/components/tables/TransactionsTable.vue'

// Chart Components
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue'
import AssetsBarTrended from '@/components/charts/AssetsBarTrended.vue'
import AccountsReorderChart from '@/components/charts/AccountsReorderChart.vue'
import AccountBalanceHistoryChart from '@/components/charts/AccountBalanceHistoryChart.vue'

// Widget Components
import RefreshTellerControls from '@/components/widgets/RefreshTellerControls.vue'
import RefreshPlaidControls from '@/components/widgets/RefreshPlaidControls.vue'

// Routing
const route = useRoute()
const router = useRouter()
const accountId = route.params.accountId || 'acc1'

// State
const selectedProducts = ref([])
const showTokenForm = ref(false)
const showPlaidRefresh = ref(false)
const showTellerRefresh = ref(false)

// Refs
const reorderChart = ref(null)

// Data
const netSummary = ref({ income: 0, expense: 0, net: 0 })
const recentTransactions = ref([])
const accountHistory = ref([])
const selectedRange = ref('30d')

// Loading/Error States
const loadingSummary = ref(false)
const loadingTransactions = ref(false)
const loadingHistory = ref(false)
const summaryError = ref(null)
const transactionsError = ref(null)
const historyError = ref(null)

// Methods
function toggleManualTokenMode() {
  showTokenForm.value = !showTokenForm.value
}

function refreshCharts() {
  reorderChart.value?.refresh?.()
}

function navigateToPlanning() {
  router.push({ name: 'Planning', query: { accountId } })
}

async function loadHistory() {
  loadingHistory.value = true
  try {
    const res = await fetchAccountHistory(accountId, selectedRange.value)
    accountHistory.value = res.balances || []
  } catch (e) {
    historyError.value = e
  } finally {
    loadingHistory.value = false
  }
}

async function loadData() {
  loadingSummary.value = true
  loadingTransactions.value = true
  loadingHistory.value = true
  
  try {
    const res = await fetchNetChanges(accountId)
    if (res?.status === 'success') {
      netSummary.value = res.data
    }
  } catch (e) {
    summaryError.value = e
  } finally {
    loadingSummary.value = false
  }

  try {
    const res = await fetchRecentTransactions(accountId, 10)
    const payload = res.data || res
    recentTransactions.value = payload.transactions || []
  } catch (e) {
    transactionsError.value = e
  } finally {
    loadingTransactions.value = false
  }

  await loadHistory()
}

// Lifecycle and watchers
onMounted(loadData)

watch(selectedRange, loadHistory)

// Add watcher for account ID changes to reload data
watch(() => route.params.accountId, (newAccountId) => {
  if (newAccountId) {
    accountId.value = newAccountId
    loadData()
  }
})
</script>

