<!-- Accounts.vue - Manage linked accounts and related actions. -->
<template>
  <AppLayout>
    <TabbedPageLayout
      class="accounts-page"
      :tabs="tabs"
      v-model="activeTab"
      sidebar-width="w-72 md:w-80"
    >
      <template #header>
        <PageHeader :icon="Wallet">
          <template #title>Accounts</template>
          <template #subtitle>Link and refresh your accounts</template>
          <template #actions>
            <UiButton variant="primary" @click="navigateToPlanning">Plan Account</UiButton>
          </template>
        </PageHeader>
      </template>

      <template #sidebar>
        <AccountActionsSidebar />
      </template>

      <template #Summary>
        <section class="space-y-6">
          <Card class="p-6">
            <h2 class="text-xl font-semibold mb-4">Net Change Summary</h2>
            <SkeletonCard v-if="loadingSummary" />
            <RetryError
              v-else-if="summaryError"
              message="Failed to load summary"
              @retry="loadData"
            />
            <div v-else class="flex justify-around">
              <div>
                Income:
                <span class="font-bold text-accent-green">{{
                  formatAmount(netSummary.income)
                }}</span>
              </div>
              <div>
                Expense:
                <span class="font-bold text-accent-red">{{
                  formatAmount(netSummary.expense)
                }}</span>
              </div>
              <div>
                Net:
                <span class="font-bold text-accent-yellow">{{ formatAmount(netSummary.net) }}</span>
              </div>
            </div>
          </Card>

          <Card class="p-6 space-y-4">
            <div class="flex justify-between items-center">
              <h2 class="text-xl font-semibold">Balance History</h2>
              <div class="flex gap-2" data-testid="history-range-controls">
                <button
                  v-for="range in ranges"
                  :key="range"
                  @click="selectedRange = range"
                  :class="['btn btn-sm', selectedRange === range ? '' : 'btn-outline']"
                >
                  {{ range }}
                </button>
              </div>
            </div>
            <SkeletonCard v-if="loadingHistory" />
            <RetryError
              v-else-if="historyError"
              message="Failed to load history"
              @retry="loadHistory"
            />
            <AccountBalanceHistoryChart
              v-else
              :balances="accountHistory"
              data-testid="history-chart"
            />
          </Card>
        </section>
      </template>

      <template #Transactions>
        <Card class="p-6 space-y-4">
          <h2 class="text-xl font-semibold">Recent Transactions</h2>
          <SkeletonCard v-if="loadingTransactions" />
          <RetryError
            v-else-if="transactionsError"
            message="Failed to load transactions"
            @retry="loadData"
          />
          <TransactionsTable v-else :transactions="recentTransactions" />
        </Card>
      </template>

      <template #Charts>
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
      </template>

      <template #Accounts>
        <Card class="p-6">
          <h2 class="text-xl font-semibold mb-4">Accounts</h2>
          <AccountsTable @refresh="refreshCharts" />
        </Card>
      </template>
    </TabbedPageLayout>
    <template #footer>
      <AppFooter />
    </template>
  </AppLayout>
</template>

<script setup>
// Dependencies and 3rd party
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Wallet } from 'lucide-vue-next'
import { fetchNetChanges, fetchRecentTransactions, fetchAccountHistory, rangeToDates } from '@/api/accounts'
import { formatAmount } from '@/utils/format'

// UI Components
import UiButton from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import SkeletonCard from '@/components/ui/SkeletonCard.vue'
import RetryError from '@/components/errors/RetryError.vue'

// Layout and sidebar
import TabbedPageLayout from '@/components/layout/TabbedPageLayout.vue'
import AccountActionsSidebar from '@/components/forms/AccountActionsSidebar.vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import AppFooter from '@/components/layout/AppFooter.vue'

// Business Components
import AccountsTable from '@/components/tables/AccountsTable.vue'
import TransactionsTable from '@/components/tables/TransactionsTable.vue'

// Chart Components
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue'
import AssetsBarTrended from '@/components/charts/AssetsBarTrended.vue'
import AccountsReorderChart from '@/components/charts/AccountsReorderChart.vue'
import AccountBalanceHistoryChart from '@/components/charts/AccountBalanceHistoryChart.vue'

// Routing
const route = useRoute()
const router = useRouter()
const accountId = ref(route.params.accountId || 'acc1')

// Tabs
const tabs = ['Summary', 'Transactions', 'Charts', 'Accounts']
const activeTab = ref('Summary')

// Refs
const reorderChart = ref(null)

// Data
const netSummary = ref({ income: 0, expense: 0, net: 0 })
const recentTransactions = ref([])
const accountHistory = ref([])
const selectedRange = ref('30d')
const ranges = ['7d', '30d', '90d', '365d']

// Loading/Error States
const loadingSummary = ref(false)
const loadingTransactions = ref(false)
const loadingHistory = ref(false)
const summaryError = ref(null)
const transactionsError = ref(null)
const historyError = ref(null)

// Methods
function refreshCharts() {
  reorderChart.value?.refresh?.()
}

function navigateToPlanning() {
  router.push({ name: 'Planning', query: { accountId: accountId.value } })
}

async function loadHistory() {
  historyError.value = null
  loadingHistory.value = true
  try {
    const { start, end } = rangeToDates(selectedRange.value)
    const res = await fetchAccountHistory(accountId.value, start, end)
    accountHistory.value = res.balances || []
  } catch (e) {
    historyError.value = e
  } finally {
    loadingHistory.value = false
  }
}

async function loadData() {
  summaryError.value = null
  transactionsError.value = null
  historyError.value = null
  loadingSummary.value = true
  loadingTransactions.value = true
  loadingHistory.value = true

  try {
    const res = await fetchNetChanges(accountId.value)
    if (res?.status === 'success') {
      netSummary.value = res.data
    }
  } catch (e) {
    summaryError.value = e
  } finally {
    loadingSummary.value = false
  }

  try {
    const res = await fetchRecentTransactions(accountId.value, 10)
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

// Reload when account ID changes
watch(
  () => route.params.accountId,
  (newAccountId) => {
    if (newAccountId) {
      accountId.value = newAccountId
      loadData()
    }
  },
)
</script>
