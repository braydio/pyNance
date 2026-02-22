<!-- Accounts.vue -->
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

      <div
        class="mt-6 h-1 w-full rounded-full bg-gradient-to-r from-[var(--color-accent-cyan)] via-[var(--color-accent-purple)] to-[var(--color-accent-magenta)]"
      />

      <div
        class="mt-4 flex flex-col gap-2 rounded-xl border border-[var(--divider)] bg-[var(--themed-bg)] p-4 sm:flex-row sm:items-center sm:justify-between"
      >
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

          <option v-for="account in accounts" :key="account.account_id" :value="account.account_id">
            {{
              account.display_name ||
              (account.mask ? `${account.name} •••• ${account.mask}` : account.name)
            }}
          </option>
        </select>
      </div>
    </template>

    <!-- SUMMARY TAB -->
    <template #Summary>
      <section class="accounts-tab-panel space-y-8">
        <Card
          v-if="!hasAccounts"
          class="accounts-card accounts-card--secondary rounded-2xl p-6 shadow-xl"
        >
          <h2 class="accounts-panel-title">No accounts linked</h2>
          <p class="mt-2 text-sm text-muted">
            Link an account to view summary, transactions, and chart data.
          </p>
        </Card>

        <template v-else>
          <Card class="accounts-card accounts-card--primary space-y-6 rounded-2xl p-6 shadow-xl">
            <header class="flex justify-between items-center">
              <div>
                <h2 class="accounts-panel-title">Net Change Summary</h2>
                <p class="text-sm text-muted">Performance for the selected date range.</p>
              </div>

              <UiButton
                variant="outline"
                class="btn-sm"
                @click="refreshSelectedAccountData"
                :disabled="!canFetchAccountData"
              >
                Refresh
              </UiButton>
            </header>

            <SkeletonCard v-if="loadingSummary" />
            <RetryError
              v-else-if="summaryError"
              message="Failed to load summary"
              @retry="retrySummary"
            />

            <div v-else class="grid gap-4 md:grid-cols-3">
              <article
                v-for="stat in netSummaryStats"
                :key="stat.key"
                class="accounts-kpi-card rounded-xl p-4"
              >
                <p class="text-xs uppercase text-muted">
                  {{ stat.label }}
                </p>
                <p class="mt-3 text-3xl font-bold" :class="stat.valueClass">
                  {{ stat.value }}
                </p>
              </article>
            </div>
          </Card>

          <Card class="accounts-card accounts-card--secondary space-y-6 rounded-2xl p-6 shadow-xl">
            <div class="flex items-center justify-between">
              <h2 class="accounts-panel-title">Balance History</h2>

              <select v-model="selectedRange" class="input w-32" :disabled="!canFetchAccountData">
                <option v-for="range in ranges" :key="range" :value="range">
                  {{ range }}
                </option>
              </select>
            </div>

            <SkeletonCard v-if="loadingHistory" />
            <RetryError
              v-else-if="historyError"
              message="Failed to load history"
              @retry="retryHistory"
            />

            <AccountBalanceHistoryChart
              v-else
              :history-data="accountHistory"
              :selected-range="selectedRange"
            />
          </Card>

          <Card class="accounts-card accounts-card--tertiary space-y-6 rounded-2xl p-6 shadow-xl">
            <h2 class="accounts-panel-title">Manage Linked Accounts</h2>
            <LinkedAccountsSection
              :accounts="linkedAccounts"
              :use-demo-fallback="false"
              :enable-promotion-editor="false"
              @add-promotion="handleAddPromotion"
            />
          </Card>
        </template>
      </section>
    </template>

    <!-- TRANSACTIONS TAB -->
    <template #Transactions>
      <section class="accounts-tab-panel">
        <Card class="accounts-card accounts-card--secondary space-y-6 rounded-2xl p-6 shadow-xl">
          <div class="flex justify-between items-center">
            <h2 class="accounts-panel-title">Activity</h2>

            <UiButton
              variant="outline"
              class="btn-sm"
              @click="retryTransactions"
              :disabled="!canFetchAccountData"
            >
              Refresh
            </UiButton>
          </div>

          <SkeletonCard v-if="loadingTransactions" />
          <RetryError
            v-else-if="transactionsError"
            message="Failed to load transactions"
            @retry="retryTransactions"
          />

          <TransactionsTable v-else :transactions="recentTransactions" />
        </Card>
      </section>
    </template>

    <!-- CHARTS TAB -->
    <template #Charts>
      <section class="accounts-tab-panel space-y-8">
        <header class="space-y-2">
          <h2 class="accounts-panel-title">Analysis</h2>
          <p class="text-sm text-muted">
            Utilities and comparisons for deeper account trend analysis.
          </p>
        </header>

        <div class="grid gap-6 lg:grid-cols-3">
          <Card class="accounts-card accounts-card--tertiary space-y-4 p-6">
            <h3 class="accounts-subpanel-title">Net Year Comparison</h3>
            <NetYearComparisonChart />
          </Card>

          <Card class="accounts-card accounts-card--tertiary space-y-4 p-6">
            <h3 class="accounts-subpanel-title">Asset Trend</h3>
            <AssetsBarTrended />
          </Card>

          <Card class="accounts-card accounts-card--tertiary space-y-4 p-6">
            <h3 class="accounts-subpanel-title">Account Order Insights</h3>
            <AccountsReorderChart />
          </Card>
        </div>
      </section>
    </template>

    <template #sidebar>
      <AccountActionsSidebar />
    </template>
  </TabbedPageLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useToast } from 'vue-toastification'
import { useRoute } from 'vue-router'
import { Wallet } from 'lucide-vue-next'

import api from '@/services/api'
import {
  fetchNetChanges,
  fetchAccountHistory,
  fetchRecentTransactions,
  rangeToDates,
} from '@/api/accounts'

import { formatAmount } from '@/utils/format'
import UiButton from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import SkeletonCard from '@/components/ui/SkeletonCard.vue'
import RetryError from '@/components/errors/RetryError.vue'
import TabbedPageLayout from '@/components/layout/TabbedPageLayout.vue'
import TransactionsTable from '@/components/tables/TransactionsTable.vue'
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue'
import AssetsBarTrended from '@/components/charts/AssetsBarTrended.vue'
import AccountsReorderChart from '@/components/charts/AccountsReorderChart.vue'
import AccountBalanceHistoryChart from '@/components/charts/AccountBalanceHistoryChart.vue'
import LinkedAccountsSection from '@/components/accounts/LinkedAccountsSection.vue'
import AccountActionsSidebar from '@/components/forms/AccountActionsSidebar.vue'

const route = useRoute()
const toast = useToast()

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

const activeTab = ref('Summary')

const hasAccounts = computed(() => accounts.value.length > 0)
const linkedAccounts = computed(() =>
  accounts.value.map((account) => ({
    id: String(account.account_id),
    name: account.display_name || account.name || 'Unnamed account',
    institution: account.institution_name || account.institution || 'Unknown Institution',
    type: account.type || account.account_type || 'Other',
    subtype: account.subtype || account.account_subtype || '',
    mask: account.mask || '',
    apr: account.apr,
    balance: account.current_balance ?? account.balance,
    limit: account.limit,
    status: account.status,
    promotions: account.promotions || [],
  })),
)
const canFetchAccountData = computed(() => hasAccounts.value && Boolean(accountId.value))

const tabs = computed(() => [
  'Summary',
  { label: 'Transactions', slot: 'Transactions', disabled: !canFetchAccountData.value },
  { label: 'Charts', slot: 'Charts', disabled: !canFetchAccountData.value },
])

const netSummaryStats = computed(() => [
  {
    key: 'income',
    label: 'Income',
    value: formatAmount(netSummary.value.income),
    valueClass: 'text-green-500',
  },
  {
    key: 'expense',
    label: 'Expense',
    value: formatAmount(netSummary.value.expense),
    valueClass: 'text-red-500',
  },
  {
    key: 'net',
    label: 'Net',
    value: formatAmount(netSummary.value.net),
    valueClass: 'text-yellow-500',
  },
])

function handleAccountSelection(e) {
  accountId.value = e.target.value || null
}

async function loadAccounts() {
  accountsLoading.value = true
  try {
    const resp = await api.getAccounts({ include_hidden: true })
    accounts.value = resp?.accounts || []
  } finally {
    accountsLoading.value = false
  }
}

async function loadData() {
  if (!canFetchAccountData.value) return

  const { start, end } = rangeToDates(selectedRange.value)

  loadingSummary.value = true
  loadingHistory.value = true
  loadingTransactions.value = true

  try {
    const [summary, history, transactions] = await Promise.all([
      fetchNetChanges(accountId.value, { start_date: start, end_date: end }),
      fetchAccountHistory(accountId.value, start, end),
      fetchRecentTransactions(accountId.value, 10),
    ])

    netSummary.value = {
      income: Number(summary?.income ?? 0),
      expense: Number(summary?.expense ?? 0),
      net: Number(summary?.net ?? 0),
    }

    accountHistory.value = history?.balances ?? []
    recentTransactions.value = transactions?.transactions ?? []
  } catch (err) {
    summaryError.value = err
    historyError.value = err
    transactionsError.value = err
  } finally {
    loadingSummary.value = false
    loadingHistory.value = false
    loadingTransactions.value = false
  }
}

function refreshSelectedAccountData() {
  loadData()
}

function retrySummary() {
  loadData()
}

function retryHistory() {
  loadData()
}

function retryTransactions() {
  loadData()
}

function handleAddPromotion() {
  toast.error('Promotion persistence is not available yet. Changes remain local drafts.')
}

onMounted(async () => {
  await loadAccounts()
  if (!accountId.value && accounts.value.length) {
    accountId.value = accounts.value[0].account_id
  }
  await loadData()
})

watch(accountId, loadData)
watch(selectedRange, loadData)
</script>
<style scoped>
.accounts-tab-panel {
  margin-top: var(--space-8, 2rem);
}

.accounts-panel-title {
  font-size: var(--font-size-4xl, 2rem);
  font-weight: var(--font-weight-bold, 700);
  line-height: 1.2;
  color: var(--theme-fg);
}

.accounts-subpanel-title {
  font-size: var(--font-size-2xl, 1.5rem);
  font-weight: var(--font-weight-semibold, 600);
  line-height: 1.3;
  color: var(--theme-fg);
}

.accounts-card {
  border: 1px solid var(--themed-border);
  background: var(--themed-bg);
}

.accounts-card--primary {
  background:
    linear-gradient(
      135deg,
      color-mix(in srgb, var(--color-accent-cyan) 20%, transparent),
      color-mix(in srgb, var(--color-accent-purple) 14%, transparent)
    ),
    var(--themed-bg);
  border-color: color-mix(in srgb, var(--color-accent-cyan) 35%, var(--themed-border));
}

.accounts-card--secondary {
  border-color: var(--themed-border);
}

.accounts-card--tertiary {
  background: var(--table-surface-strong);
  border-color: var(--table-border);
}

.accounts-kpi-card {
  border: 1px solid var(--themed-border);
  background: var(--table-surface);
}
</style>
