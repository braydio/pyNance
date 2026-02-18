<template>
  <TabbedPageLayout
    class="accounts-page"
    :tabs="tabs"
    v-model="activeTab"
    sidebar-width="w-72 md:w-80"
  >
    <!-- HEADER -->
    <template #header>
      <PageHeader :icon="Wallet">
        <template #title>Accounts</template>
        <template #subtitle>Link and refresh your accounts</template>
      </PageHeader>

      <div class="mt-4 flex flex-col gap-2 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between">
        <label class="text-sm font-medium text-muted">Viewing account</label>

        <select
          class="input w-full sm:w-80"
          :value="accountId || ''"
          :disabled="accountsLoading || !hasAccounts"
          @change="handleAccountSelection"
        >
          <option value="" :disabled="hasAccounts">
            {{ hasAccounts ? 'Select an account' : 'No accounts available' }}
          </option>

          <option
            v-for="account in accounts"
            :key="account.account_id"
            :value="account.account_id"
          >
            {{ account.mask ? `${account.name} •••• ${account.mask}` : account.name }}
          </option>
        </select>
      </div>
    </template>

    <template #sidebar v-if="showActionsSidebar">
      <AccountActionsSidebar />
    </template>

    <!-- OVERVIEW -->
    <template #Overview>
      <section v-if="!hasAccounts" class="space-y-6">
        <Card class="p-6">
          <h2 class="text-xl font-semibold">No accounts linked</h2>
          <p class="text-sm text-muted mt-2">
            Link an account to view summary and history.
          </p>
        </Card>
      </section>

      <section v-else class="space-y-6">
        <Card class="p-6 space-y-4">
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-semibold">Net Change Summary</h2>

            <UiButton
              variant="outline"
              @click="refreshSelectedAccountData"
              :disabled="!canFetchAccountData"
            >
              Refresh
            </UiButton>
          </div>

          <SkeletonCard v-if="loadingSummary" />

          <RetryError
            v-else-if="summaryError"
            message="Failed to load summary"
            @retry="refreshSelectedAccountData"
          />

          <div v-else class="grid md:grid-cols-3 gap-4">
            <div
              v-for="stat in netSummaryStats"
              :key="stat.key"
              class="rounded-xl border p-4"
            >
              <p class="text-xs uppercase text-muted">{{ stat.label }}</p>
              <p class="text-2xl font-bold mt-2">{{ stat.value }}</p>
              <p class="text-xs text-muted mt-1">{{ stat.helper }}</p>
            </div>
          </div>
        </Card>

        <Card class="p-6 space-y-4">
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-semibold">Balance History</h2>

            <select
              v-model="selectedRange"
              class="input w-32"
              :disabled="!canFetchAccountData"
            >
              <option v-for="range in ranges" :key="range" :value="range">
                {{ range }}
              </option>
            </select>
          </div>

          <SkeletonCard v-if="loadingHistory" />

          <RetryError
            v-else-if="historyError"
            message="Failed to load history"
            @retry="loadHistory"
          />

          <AccountBalanceHistoryChart
            v-else
            :history-data="accountHistory"
            :selected-range="selectedRange"
          />
        </Card>
      </section>
    </template>

    <!-- ACTIVITY -->
    <template #Activity>
      <Card class="p-6 space-y-4">
        <div class="flex justify-between items-center">
          <h2 class="text-xl font-semibold">Activity</h2>

          <UiButton
            variant="outline"
            @click="refreshSelectedAccountData"
            :disabled="!canFetchAccountData"
          >
            Refresh
          </UiButton>
        </div>

        <SkeletonCard v-if="loadingTransactions" />

        <RetryError
          v-else-if="transactionsError"
          message="Failed to load transactions"
          @retry="refreshSelectedAccountData"
        />

        <TransactionsTable v-else :transactions="recentTransactions" />
      </Card>
    </template>

    <!-- ANALYSIS -->
    <template #Analysis>
      <section class="grid gap-6 lg:grid-cols-3">
        <Card class="p-6">
          <NetYearComparisonChart />
        </Card>

        <Card class="p-6">
          <AssetsBarTrended />
        </Card>

        <Card class="p-6">
          <AccountsReorderChart ref="reorderChart" />
        </Card>
      </section>
    </template>

    <!-- MANAGE -->
    <template #Manage>
      <section class="space-y-6">
        <LinkedAccountsSection />
        <AccountsTable />
      </section>
    </template>
  </TabbedPageLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Wallet } from 'lucide-vue-next'
import api from '@/services/api'
import {
  fetchNetChanges,
  fetchAccountHistory,
  fetchRecentTransactions,
  rangeToDates,
} from '@/api/accounts'
import { formatAmount } from '@/utils/format'
import { useAccountPreferences } from '@/stores/useAccountPreferences'

import UiButton from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import SkeletonCard from '@/components/ui/SkeletonCard.vue'
import RetryError from '@/components/errors/RetryError.vue'
import TabbedPageLayout from '@/components/layout/TabbedPageLayout.vue'
import AccountActionsSidebar from '@/components/forms/AccountActionsSidebar.vue'
import AccountsTable from '@/components/tables/AccountsTable.vue'
import LinkedAccountsSection from '@/components/accounts/LinkedAccountsSection.vue'
import TransactionsTable from '@/components/tables/TransactionsTable.vue'
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue'
import AssetsBarTrended from '@/components/charts/AssetsBarTrended.vue'
import AccountsReorderChart from '@/components/charts/AccountsReorderChart.vue'
import AccountBalanceHistoryChart from '@/components/charts/AccountBalanceHistoryChart.vue'

const route = useRoute()
const router = useRouter()
const accountPrefs = useAccountPreferences()

const activeTab = ref('Overview')
const tabs = ['Overview', 'Activity', 'Analysis', 'Manage']

const accounts = ref([])
const accountsLoading = ref(false)
const accountId = ref(route.query.accountId?.toString() || null)

const netSummary = ref({ income: 0, expense: 0, net: 0 })
const accountHistory = ref([])
const recentTransactions = ref([])

const ranges = ['7d', '30d', '90d', '365d']
const selectedRange = ref('30d')

const loadingSummary = ref(false)
const loadingHistory = ref(false)
const loadingTransactions = ref(false)

const summaryError = ref(null)
const historyError = ref(null)
const transactionsError = ref(null)

const hasAccounts = computed(() => accounts.value.length > 0)
const canFetchAccountData = computed(
  () => hasAccounts.value && Boolean(accountId.value),
)

const showActionsSidebar = computed(
  () => activeTab.value === 'Overview' || activeTab.value === 'Manage',
)

const netSummaryStats = computed(() => [
  {
    key: 'income',
    label: 'Income',
    value: formatAmount(netSummary.value.income),
    helper: 'Total deposits',
  },
  {
    key: 'expense',
    label: 'Expense',
    value: formatAmount(netSummary.value.expense),
    helper: 'Total spending',
  },
  {
    key: 'net',
    label: 'Net Change',
    value: formatAmount(netSummary.value.net),
    helper: 'Income − Expense',
  },
])

async function loadAccounts() {
  accountsLoading.value = true
  try {
    const resp = await api.getAccounts({ include_hidden: true })
    accounts.value = resp?.accounts || []
  } finally {
    accountsLoading.value = false
  }
}

function handleAccountSelection(event) {
  accountId.value = event.target.value || null
}

async function refreshSelectedAccountData() {
  if (!canFetchAccountData.value) return

  const { start, end } = rangeToDates(selectedRange.value)

  loadingSummary.value = true
  loadingTransactions.value = true
  loadingHistory.value = true

  try {
    const summary = await fetchNetChanges(accountId.value, {
      start_date: start,
      end_date: end,
    })
    netSummary.value = summary?.data || netSummary.value
  } catch (e) {
    summaryError.value = e
  } finally {
    loadingSummary.value = false
  }

  try {
    const history = await fetchAccountHistory(accountId.value, start, end)
    accountHistory.value = history?.balances || []
  } catch (e) {
    historyError.value = e
  } finally {
    loadingHistory.value = false
  }

  try {
    const tx = await fetchRecentTransactions(accountId.value, 10)
    recentTransactions.value = tx?.transactions || []
  } catch (e) {
    transactionsError.value = e
  } finally {
    loadingTransactions.value = false
  }
}

onMounted(async () => {
  await loadAccounts()
  if (!accountId.value && accounts.value.length) {
    accountId.value = accounts.value[0].account_id
  }
  await refreshSelectedAccountData()
})

watch(accountId, async () => {
  router.replace({ query: { ...route.query, accountId: accountId.value } })
  await refreshSelectedAccountData()
})

watch(selectedRange, async () => {
  if (accountId.value) {
    accountPrefs.setSelectedRange(accountId.value, selectedRange.value)
  }
  await refreshSelectedAccountData()
})
</script>

