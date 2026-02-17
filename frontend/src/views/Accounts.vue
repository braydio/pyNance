<!-- Accounts.vue - Manage linked accounts and related actions. -->
<template>
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
          <UiButton
            variant="primary"
            class="shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
            @click="navigateToPlanning"
          >
            Plan Account
          </UiButton>
        </template>
      </PageHeader>
      <div
        class="mt-6 h-1 w-full rounded-full bg-gradient-to-r from-[var(--color-accent-cyan)] via-[var(--color-accent-purple)] to-[var(--color-accent-magenta)]"
      />
      <div
        class="mt-4 flex flex-col gap-2 rounded-xl border border-[var(--divider)] bg-[var(--themed-bg)] p-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <label class="text-sm font-medium text-muted" for="account-context-selector"
          >Viewing account</label
        >
        <select
          id="account-context-selector"
          class="input w-full sm:w-80"
          :value="accountId || ''"
          :disabled="accountsLoading || !hasAccounts"
          data-testid="account-context-selector"
          @change="handleAccountSelection"
        >
          <option value="" :disabled="hasAccounts">
            {{ hasAccounts ? 'Select an account' : 'No accounts available' }}
          </option>
          <option v-for="account in accounts" :key="account.account_id" :value="account.account_id">
            {{ account.mask ? `${account.name} •••• ${account.mask}` : account.name }}
          </option>
        </select>
      </div>
    </template>

    <template #sidebar>
      <AccountActionsSidebar />
    </template>

    <template #Summary>
      <section class="space-y-8">
        <Card
          v-if="!hasAccounts"
          class="rounded-2xl border border-[var(--divider)] bg-[var(--themed-bg)] p-6 shadow-xl"
          data-testid="accounts-summary-empty"
        >
          <h2 class="text-2xl font-semibold text-[var(--color-accent-cyan)]">No accounts linked</h2>
          <p class="mt-2 text-sm text-muted">
            Link an account to view summary, transactions, and chart data.
          </p>
        </Card>

        <template v-else>
          <Card class="summary-card space-y-6 rounded-2xl border p-6 shadow-xl">
            <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 class="text-2xl font-semibold text-[var(--color-accent-cyan)]">
                  Net Change Summary
                </h2>
                <p class="text-sm text-muted">
                  Performance for the selected date range across your linked accounts.
                </p>
              </div>
              <UiButton
                variant="outline"
                class="btn-sm whitespace-nowrap shadow-sm transition hover:-translate-y-0.5"
                @click="refreshSelectedAccountData"
                :disabled="!canFetchAccountData"
              >
                Refresh Overview
              </UiButton>
            </header>

            <SkeletonCard v-if="loadingSummary" />
            <RetryError
              v-else-if="summaryError"
              message="Failed to load summary"
              @retry="refreshSelectedAccountData"
            />
            <div v-else class="grid gap-4 md:grid-cols-3" data-testid="net-summary-cards">
              <article
                v-for="stat in netSummaryStats"
                :key="stat.key"
                class="summary-card__stat rounded-xl border p-4 shadow-inner transition hover:shadow-lg"
                :class="stat.containerClass"
              >
                <p class="text-xs font-semibold uppercase tracking-wide text-muted">
                  {{ stat.label }}
                </p>
                <p class="mt-3 text-3xl font-bold" :class="stat.valueClass">{{ stat.value }}</p>
                <p v-if="stat.helper" class="mt-2 text-xs text-muted">{{ stat.helper }}</p>
              </article>
            </div>
          </Card>

          <Card
            class="space-y-6 rounded-2xl border border-[var(--divider)] bg-[var(--themed-bg)] p-6 shadow-xl"
          >
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 class="text-2xl font-semibold text-[var(--color-accent-purple)]">
                  Balance History
                </h2>
                <p class="text-sm text-muted">
                  Track balances across your preferred reporting window.
                </p>
              </div>
              <label class="flex items-center gap-3 text-sm text-muted">
                <span>Range</span>
                <select
                  v-model="selectedRange"
                  class="input w-32"
                  data-testid="history-range-select"
                  :disabled="!canFetchAccountData"
                >
                  <option v-for="range in ranges" :key="range" :value="range">
                    {{ range }}
                  </option>
                </select>
              </label>
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
              data-testid="history-chart"
            />
          </Card>
        </template>
      </section>
    </template>

    <template #Transactions>
      <Card
        class="space-y-6 rounded-2xl border border-[var(--divider)] bg-[var(--themed-bg)] p-6 shadow-xl"
      >
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 class="text-2xl font-semibold text-[var(--color-accent-cyan)]">
              Recent Transactions
            </h2>
            <p class="text-sm text-muted">Latest activity from accounts linked to your profile.</p>
          </div>
          <UiButton
            variant="outline"
            class="btn-sm whitespace-nowrap shadow-sm transition hover:-translate-y-0.5"
            @click="refreshSelectedAccountData"
            :disabled="!canFetchAccountData"
          >
            Refresh List
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

    <template #Charts>
      <section class="space-y-8">
        <header class="space-y-2">
          <h2 class="text-2xl font-semibold text-[var(--color-accent-purple)]">Account Analysis</h2>
          <p class="text-sm text-muted">
            Visualize account health, year-over-year change, and asset distribution.
          </p>
        </header>
        <div class="grid gap-6 lg:grid-cols-3">
          <Card
            class="space-y-4 rounded-2xl border border-[var(--divider)] bg-gradient-to-br from-[rgba(99,205,207,0.08)] to-[rgba(113,156,214,0.05)] p-6 shadow-lg"
          >
            <h3 class="text-lg font-semibold text-[var(--color-accent-cyan)]">Year Comparison</h3>
            <NetYearComparisonChart />
          </Card>
          <Card
            class="space-y-4 rounded-2xl border border-[var(--divider)] bg-[var(--themed-bg)] p-6 shadow-lg"
          >
            <h3 class="text-lg font-semibold text-[var(--color-accent-yellow)]">Assets Trend</h3>
            <AssetsBarTrended />
          </Card>
          <Card
            class="space-y-4 rounded-2xl border border-[var(--divider)] bg-[var(--themed-bg)] p-6 shadow-lg"
          >
            <h3 class="text-lg font-semibold text-[var(--color-accent-green)]">
              Account Balance Distribution
            </h3>
            <AccountsReorderChart ref="reorderChart" />
          </Card>
        </div>
      </section>
    </template>

    <template #AccountDetails>
      <section class="space-y-8">
        <LinkedAccountsSection />
        <Card
          class="space-y-4 rounded-2xl border border-[var(--divider)] bg-[var(--themed-bg)] p-6 shadow-xl"
        >
          <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <h2 class="text-2xl font-semibold text-[var(--color-accent-cyan)]">Accounts</h2>
            <p class="text-sm text-muted">
              Manage visibility, details, and refresh status for each institution.
            </p>
          </div>
          <AccountsTable @refresh="refreshCharts" />
        </Card>
      </section>
    </template>
  </TabbedPageLayout>
</template>

<script setup>
// Dependencies and 3rd party
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { Wallet } from 'lucide-vue-next'
import {
  fetchNetChanges,
  fetchRecentTransactions,
  fetchAccountHistory,
  rangeToDates,
} from '@/api/accounts'
import { formatAmount } from '@/utils/format'
import { useAccountPreferences } from '@/stores/useAccountPreferences'

// UI Components
import UiButton from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import SkeletonCard from '@/components/ui/SkeletonCard.vue'
import RetryError from '@/components/errors/RetryError.vue'

// Layout and sidebar
import TabbedPageLayout from '@/components/layout/TabbedPageLayout.vue'
import AccountActionsSidebar from '@/components/forms/AccountActionsSidebar.vue'

// Business Components
import AccountsTable from '@/components/tables/AccountsTable.vue'
import LinkedAccountsSection from '@/components/accounts/LinkedAccountsSection.vue'
import TransactionsTable from '@/components/tables/TransactionsTable.vue'

// Chart Components
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue'
import AssetsBarTrended from '@/components/charts/AssetsBarTrended.vue'
import AccountsReorderChart from '@/components/charts/AccountsReorderChart.vue'
import AccountBalanceHistoryChart from '@/components/charts/AccountBalanceHistoryChart.vue'

// Routing
const route = useRoute()
const router = useRouter()
const accountId = ref(route.query.accountId?.toString() || null)
const accountPrefs = useAccountPreferences()

// Tabs
const activeTab = ref('Summary')

// Refs
const reorderChart = ref(null)

// Data
const accounts = ref([])
const accountsLoading = ref(false)
const netSummary = ref({ income: 0, expense: 0, net: 0 })
const recentTransactions = ref([])
const accountHistory = ref([])
const ranges = ['7d', '30d', '90d', '365d']
const selectedRange = ref('30d')

// Loading/Error States
const loadingSummary = ref(false)
const loadingTransactions = ref(false)
const loadingHistory = ref(false)
const summaryError = ref(null)
const transactionsError = ref(null)
const historyError = ref(null)

const hasAccounts = computed(() => accounts.value.length > 0)
const hasSelectedAccount = computed(() => Boolean(accountId.value))
const canFetchAccountData = computed(() => hasAccounts.value && hasSelectedAccount.value)

const tabs = computed(() => [
  { label: 'Account Details', slot: 'AccountDetails' },
  'Summary',
  { label: 'Transactions', slot: 'Transactions', disabled: !canFetchAccountData.value },
  { label: 'Charts', slot: 'Charts', disabled: !canFetchAccountData.value },
])

const netSummaryStats = computed(() => [
  {
    key: 'income',
    label: 'Income',
    value: formatAmount(netSummary.value.income),
    containerClass: 'summary-card--income',
    valueClass: 'text-[var(--color-accent-green)]',
    helper: 'Total deposits recorded',
  },
  {
    key: 'expense',
    label: 'Expense',
    value: formatAmount(netSummary.value.expense),
    containerClass: 'summary-card--expense',
    valueClass: 'text-[var(--color-accent-red)]',
    helper: 'Total spending captured',
  },
  {
    key: 'net',
    label: 'Net Change',
    value: formatAmount(netSummary.value.net),
    containerClass: 'summary-card--net',
    valueClass: 'text-[var(--color-accent-yellow)]',
    helper: 'Overall change (income − expense)',
  },
])

function resetDataState() {
  netSummary.value = { income: 0, expense: 0, net: 0 }
  recentTransactions.value = []
  accountHistory.value = []
}

function syncRangePreference(id) {
  if (!id) {
    selectedRange.value = '30d'
    return
  }
  selectedRange.value = accountPrefs.getSelectedRange(id)
  accountPrefs.setSelectedRange(id, selectedRange.value)
}

function refreshCharts() {
  reorderChart.value?.refresh?.()
}

function navigateToPlanning() {
  if (!accountId.value) {
    return
  }
  router.push({ name: 'Planning', query: { accountId: accountId.value } })
}

function handleAccountSelection(event) {
  const nextAccountId = event.target.value || null
  if (!nextAccountId || nextAccountId === accountId.value) {
    return
  }
  accountId.value = nextAccountId
}

async function loadAccounts() {
  accountsLoading.value = true
  try {
    const resp = await api.getAccounts({ include_hidden: true })
    accounts.value = resp?.accounts || []
  } catch (_) {
    accounts.value = []
  } finally {
    accountsLoading.value = false
  }
}

function resolveInitialAccountId() {
  if (!accounts.value.length) {
    accountId.value = null
    return
  }

  const accountIds = new Set(accounts.value.map((entry) => entry.account_id))
  const routeAccountId = route.query.accountId?.toString() || null
  if (routeAccountId && accountIds.has(routeAccountId)) {
    accountId.value = routeAccountId
    return
  }

  if (accountId.value && accountIds.has(accountId.value)) {
    return
  }

  accountId.value = accounts.value[0].account_id
}

function syncRouteQuery() {
  const currentQueryAccountId = route.query.accountId?.toString() || null
  if (currentQueryAccountId === accountId.value) {
    return
  }

  const nextQuery = { ...route.query }
  if (accountId.value) {
    nextQuery.accountId = accountId.value
  } else {
    delete nextQuery.accountId
  }

  router.replace({ query: nextQuery })
}

async function loadHistory() {
  if (!canFetchAccountData.value) {
    return
  }

  historyError.value = null
  loadingHistory.value = true

  try {
    const { start, end } = rangeToDates(selectedRange.value)
    const res = await fetchAccountHistory(accountId.value, start, end)
    accountHistory.value = res.balances || []
  } catch (error) {
    historyError.value = error
  } finally {
    loadingHistory.value = false
  }
}

async function refreshSelectedAccountData() {
  if (!canFetchAccountData.value) {
    summaryError.value = null
    transactionsError.value = null
    historyError.value = null
    loadingSummary.value = false
    loadingTransactions.value = false
    loadingHistory.value = false
    resetDataState()
    return
  }

  summaryError.value = null
  transactionsError.value = null
  historyError.value = null
  loadingSummary.value = true
  loadingTransactions.value = true
  loadingHistory.value = true

  try {
    const { start, end } = rangeToDates(selectedRange.value)
    const res = await fetchNetChanges(accountId.value, {
      start_date: start,
      end_date: end,
    })
    if (res?.status === 'success') {
      netSummary.value = res.data
    }
  } catch (error) {
    summaryError.value = error
  } finally {
    loadingSummary.value = false
  }

  try {
    const res = await fetchRecentTransactions(accountId.value, 10)
    const payload = res.data || res
    recentTransactions.value = payload.transactions || []
  } catch (error) {
    transactionsError.value = error
  } finally {
    loadingTransactions.value = false
  }

  await loadHistory()
}

async function initializeAccountsView() {
  await loadAccounts()
  resolveInitialAccountId()
  syncRangePreference(accountId.value)
  syncRouteQuery()
  await refreshSelectedAccountData()
}

onMounted(initializeAccountsView)

watch(
  () => route.query.accountId,
  (newQueryAccountId) => {
    const normalizedAccountId = newQueryAccountId?.toString() || null
    if (normalizedAccountId === accountId.value) {
      return
    }

    if (!normalizedAccountId) {
      if (!accounts.value.length) {
        accountId.value = null
      }
      return
    }

    const accountExists = accounts.value.some((entry) => entry.account_id === normalizedAccountId)
    if (accountExists) {
      accountId.value = normalizedAccountId
    }
  },
)

watch(accountId, async (newAccountId, previousAccountId) => {
  if (newAccountId === previousAccountId) {
    return
  }

  syncRangePreference(newAccountId)
  syncRouteQuery()
  await refreshSelectedAccountData()
})

watch(selectedRange, async (range, previousRange) => {
  if (range === previousRange) {
    return
  }

  if (accountId.value) {
    accountPrefs.setSelectedRange(accountId.value, range)
  }

  await refreshSelectedAccountData()
})
</script>

<style scoped>
.summary-card {
  background: var(--accounts-summary-card-bg);
  border-color: var(--accounts-summary-card-border);
  backdrop-filter: blur(8px);
}

.summary-card__stat {
  background: var(--accounts-summary-stat-bg);
  border-color: var(--accounts-summary-stat-border);
  backdrop-filter: blur(10px);
}

.summary-card--income {
  background: var(--summary-card-income-bg);
  border-color: var(--summary-card-income-border);
}

.summary-card--expense {
  background: var(--summary-card-expense-bg);
  border-color: var(--summary-card-expense-border);
}

.summary-card--net {
  background: var(--summary-card-net-bg);
  border-color: var(--summary-card-net-border);
}

.accounts-hero {
  position: relative;
}

.accounts-hero__card {
  position: relative;
  overflow: hidden;
  border-radius: 1.75rem;
  border: 2px solid var(--color-accent-cyan);
  padding: clamp(1.75rem, 3vw, 2.5rem);
  background:
    linear-gradient(
      135deg,
      rgba(99, 205, 207, 0.18) 0%,
      rgba(113, 156, 214, 0.08) 42%,
      rgba(214, 122, 210, 0.12) 100%
    ),
    var(--color-bg-sec);
}

.accounts-hero__card::before,
.accounts-hero__card::after {
  content: '';
  position: absolute;
  pointer-events: none;
}

.accounts-hero__card::before {
  inset: -30% auto auto -20%;
  width: 60%;
  height: 140%;
  background: radial-gradient(
    65% 65% at 50% 50%,
    rgba(99, 205, 207, 0.45) 0%,
    rgba(99, 205, 207, 0) 100%
  );
  filter: blur(0.5rem);
}

.accounts-hero__card::after {
  inset: auto -25% -55% auto;
  width: 55%;
  height: 120%;
  background: radial-gradient(
    65% 65% at 50% 50%,
    rgba(214, 122, 210, 0.4) 0%,
    rgba(214, 122, 210, 0) 100%
  );
  filter: blur(0.5rem);
}

.accounts-hero__card :deep(.flex) {
  flex-wrap: wrap;
  gap: 1.5rem;
}

.accounts-hero__card :deep(h1) {
  font-size: clamp(2rem, 3vw, 2.75rem);
  font-weight: 700;
  letter-spacing: 0.02em;
}

.accounts-hero__card :deep(p) {
  font-size: 0.95rem;
}

.accounts-hero__cta {
  padding-inline: clamp(1.5rem, 3.5vw, 2.5rem);
  padding-block: 0.9rem;
  font-size: 0.95rem;
  border-radius: 999px;
  box-shadow: 0 14px 34px rgba(99, 205, 207, 0.35);
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease;
}

.accounts-hero__cta:hover {
  transform: translateY(-3px);
  box-shadow: 0 18px 36px rgba(99, 205, 207, 0.45);
}

.accounts-hero__divider {
  position: relative;
  height: 12px;
  border-radius: 999px;
  overflow: hidden;
  background: linear-gradient(
    90deg,
    rgba(99, 205, 207, 0.18) 0%,
    rgba(113, 156, 214, 0.25) 55%,
    rgba(214, 122, 210, 0.22) 100%
  );
  border: 1px solid rgba(99, 205, 207, 0.35);
}

.accounts-hero__divider-glow {
  position: absolute;
  inset: -60% -20% -60% -20%;
  background: radial-gradient(
    60% 60% at 50% 50%,
    rgba(99, 205, 207, 0.45) 0%,
    rgba(214, 122, 210, 0.32) 35%,
    rgba(25, 32, 56, 0) 100%
  );
  opacity: 0.8;
}

@media (max-width: 640px) {
  .accounts-hero__card {
    padding-inline: 1.5rem;
  }

  .accounts-hero__card :deep(.flex) {
    align-items: flex-start;
  }
}
</style>
