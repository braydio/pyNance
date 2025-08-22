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
      <div class="flex flex-wrap gap-4 justify-center">
        <LinkAccount :selected-products="selectedProducts" @manual-token-click="toggleManualTokenMode" />

        <UiButton variant="outline" @click="togglePlaidRefresh">
          {{ showPlaidRefresh ? 'Hide' : 'Refresh' }} Plaid Accounts
        </UiButton>
        <transition name="slide-down" mode="out-in">
          <div v-if="showPlaidRefresh" class="w-full">
            <RefreshPlaidControls />
          </div>
        </transition>

        <UiButton variant="outline" @click="toggleTellerRefresh">
          {{ showTellerRefresh ? 'Hide' : 'Refresh' }} Teller Accounts
        </UiButton>
        <transition name="slide-down" mode="out-in">
          <div v-if="showTellerRefresh" class="w-full">
            <RefreshTellerControls />
          </div>
        </transition>

        <TokenUpload v-if="showTokenForm" @cancel="toggleManualTokenMode" />
      </div>
    </Card>

    <!-- Net Change Summary -->
    <Card class="p-6">
      <div v-if="loadingSummary">Loading summary...</div>
      <div v-else-if="summaryError" class="text-error">Failed to load summary</div>
      <div v-else class="flex justify-around">
        <div>Income: <span class="font-bold text-accent-green">{{ formatAmount(netSummary.income) }}</span></div>
        <div>Expense: <span class="font-bold text-accent-red">{{ formatAmount(netSummary.expense) }}</span></div>
        <div>Net: <span class="font-bold text-accent-yellow">{{ formatAmount(netSummary.net) }}</span></div>
      </div>
    </Card>

    <!-- Balance History -->
    <section class="card p-4 bg-[var(--color-bg-secondary)] rounded-lg shadow-md space-y-4">
      <div class="flex justify-end">
        <select v-model="selectedRange" data-testid="filter-dropdown" class="border rounded p-1">
          <option value="7d">7d</option>
          <option value="30d">30d</option>
          <option value="90d">90d</option>
          <option value="365d">365d</option>
        </select>
      </div>
      <div v-if="loadingHistory">Loading...</div>
      <div v-else-if="historyError" class="text-error">Failed to load history</div>
      <AccountBalanceHistoryChart v-else :balances="accountHistory" data-testid="history-chart" />
    </section>

    <!-- Balance History -->
    <section class="card p-4 bg-[var(--color-bg-secondary)] rounded-lg shadow-md space-y-4">
      <div class="flex justify-end">
        <select v-model="selectedRange" data-testid="filter-dropdown" class="border rounded p-1">
          <option value="7d">7d</option>
          <option value="30d">30d</option>
          <option value="90d">90d</option>
          <option value="365d">365d</option>
        </select>
      </div>
      <div v-if="loadingHistory">Loading...</div>
      <div v-else-if="historyError" class="text-error">Failed to load history</div>
      <AccountBalanceHistoryChart v-else :balances="accountHistory" data-testid="history-chart" />
    </section>

    <!-- Recent Transactions -->
    <Card class="p-6 space-y-2">
      <h2 class="text-2xl font-bold">Recent Transactions</h2>
      <div v-if="loadingTransactions">Loading...</div>
      <div v-else-if="transactionsError" class="text-error">Failed to load transactions</div>
      <TransactionsTable v-else :transactions="recentTransactions" />
    </Card>

    <!-- Charts -->
    <div class="flex flex-col gap-6">
      <Card class="p-6">
        <NetYearComparisonChart />
      </Card>
      <Card class="p-6">
        <AssetsBarTrended />
      </Card>
      <Card class="p-6">
        <AccountsReorderChart ref="reorderChart" />
      </Card>
    </div>

    <!-- Accounts Table -->
    <Card class="p-6">
      <InstitutionTable @refresh="refreshCharts" />
    </Card>

    <!-- Footer -->
    <footer class="mt-12 text-center text-sm text-muted border-t pt-4">
      &copy; good dashroad.
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { fetchNetChanges, fetchRecentTransactions, fetchAccountHistory } from '@/api/accounts'
import { formatAmount } from "@/utils/format"

// State
const selectedProducts = ref([])
const showTokenForm = ref(false)
const showPlaidRefresh = ref(false)
const showTellerRefresh = ref(false)
const reorderChart = ref(null)
const route = useRoute()
const accountId = route.params.accountId || 'acc1'

// Net changes and recent transactions
const netSummary = ref({ income: 0, expense: 0, net: 0 })
const recentTransactions = ref([])
const loadingSummary = ref(false)
const loadingTransactions = ref(false)
const summaryError = ref(null)
const transactionsError = ref(null)
const accountHistory = ref([])
const selectedRange = ref('30d')
const loadingHistory = ref(false)
const historyError = ref(null)

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

onMounted(async () => {
  loadingSummary.value = true
  loadingTransactions.value = true
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
})

watch(selectedRange, loadHistory)

// Components
import LinkAccount from '@/components/forms/LinkAccount.vue'
import InstitutionTable from '@/components/tables/InstitutionTable.vue'
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue'
import AssetsBarTrended from '@/components/charts/AssetsBarTrended.vue'
import AccountsReorderChart from '@/components/charts/AccountsReorderChart.vue'
import RefreshTellerControls from '@/components/widgets/RefreshTellerControls.vue'
import RefreshPlaidControls from '@/components/widgets/RefreshPlaidControls.vue'
import TokenUpload from '@/components/forms/TokenUpload.vue'
import TransactionsTable from '@/components/tables/TransactionsTable.vue'
import AccountBalanceHistoryChart from '@/components/charts/AccountBalanceHistoryChart.vue'

import UiButton from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import { Wallet } from 'lucide-vue-next'

</script>

