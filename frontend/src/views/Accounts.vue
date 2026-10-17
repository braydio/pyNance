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
        <template #subtitle>Balances, activity, and connection health</template>
      </PageHeader>

      <div class="accounts-context" data-testid="accounts-context">
        <div class="accounts-context__row">
          <label class="sr-only" for="accounts-selector">Viewing account</label>
          <select
            id="accounts-selector"
            class="input w-full sm:w-80"
            :value="accountId || ''"
            :disabled="accountsLoading || !hasAccounts"
            @change="handleAccountSelection"
          >
            <option value="">
              {{ hasAccounts ? 'All accounts' : 'No accounts available' }}
            </option>

            <option
              v-for="account in accounts"
              :key="account.account_id"
              :value="account.account_id"
            >
              {{
                account.display_name ||
                (account.mask ? `${account.name} •••• ${account.mask}` : account.name)
              }}
            </option>
          </select>
          <UiButton
            variant="primary"
            class="btn-sm"
            data-testid="accounts-refresh"
            :disabled="!canFetchAccountData"
            @click="refreshSelectedAccountData"
          >
            Refresh
          </UiButton>
        </div>

        <p
          v-if="selectedAccountStatus"
          class="accounts-context__status"
          data-testid="account-status"
        >
          <strong>{{ selectedAccountStatus.name }}</strong>
          <span v-if="selectedAccountStatus.detail"> · {{ selectedAccountStatus.detail }}</span>
          <span v-if="selectedAccountStatus.balance"> · {{ selectedAccountStatus.balance }}</span>
          <span> · {{ selectedAccountStatus.connection }}</span>
        </p>

        <div
          v-if="attentionConnectionCount"
          class="surface-attention accounts-context__attention"
          role="status"
          data-testid="connection-attention"
        >
          <span>
            {{
              attentionConnectionCount === 1
                ? 'A connection needs to be reconnected.'
                : `${attentionConnectionCount} connections need to be reconnected.`
            }}
          </span>
          <UiButton variant="outline" class="btn-sm" @click="activeTab = 'Connections'">
            Fix connection
          </UiButton>
        </div>
      </div>
    </template>

    <!-- SUMMARY TAB -->
    <template #Summary>
      <section class="accounts-tab-panel">
        <RetryError v-if="accountsError" message="Failed to load accounts" @retry="retryAccounts" />
        <Card
          v-else-if="!hasAccounts"
          class="accounts-card accounts-card--secondary rounded-2xl p-6 shadow-xl"
        >
          <h2 class="accounts-panel-title">No accounts linked</h2>
          <p class="mt-2 text-sm text-muted">
            Link an account to view summary, transactions, and chart data.
          </p>
        </Card>

        <template v-else>
          <Card class="accounts-card accounts-card--secondary rounded-2xl p-4 shadow-xl">
            <AccountPortfolioOverview
              :accounts="accounts"
              :group="portfolioFilters.group"
              :include-hidden="portfolioFilters.includeHidden"
              @update:group="setPortfolioGroup"
            />
          </Card>

          <Card class="accounts-card accounts-card--secondary rounded-2xl p-4 shadow-xl">
            <AccountPortfolioList
              :accounts="accounts"
              :filters="portfolioFilters"
              :selected-id="accountId"
              @update:filters="portfolioFilters = $event"
              @reset="resetPortfolioFilters"
              @select="selectAccount"
            />
          </Card>

          <div class="accounts-period-bar" data-testid="accounts-period-bar">
            <label class="accounts-period-bar__label" for="accounts-period">Period</label>
            <select
              id="accounts-period"
              v-model="selectedRange"
              class="input w-32"
              data-testid="history-range-select"
            >
              <option v-for="range in ranges" :key="range" :value="range">
                {{ rangeLabels[range] }}
              </option>
            </select>
            <span class="accounts-period-bar__dates" data-testid="accounts-period-dates">
              {{ periodDates.start }} – {{ periodDates.end }}
            </span>
          </div>

          <template v-if="selectedAccount">
            <header
              id="account-details"
              ref="detailsRef"
              class="accounts-details-header"
              data-testid="account-details-header"
            >
              <h2 class="accounts-subpanel-title">
                {{ selectedAccount.display_name || selectedAccount.name }}
              </h2>
              <UiButton variant="outline" class="btn-sm" @click="clearSelectedAccount">
                Back to all accounts
              </UiButton>
            </header>

            <Card
              class="accounts-card accounts-card--secondary space-y-4 rounded-2xl p-5 shadow-xl"
              data-testid="account-focus"
            >
              <p class="text-sm text-muted" data-testid="account-focus-identity">
                {{ focus.identity }}
              </p>
              <dl class="accounts-facts">
                <div v-for="fact in focus.facts" :key="fact.label" class="accounts-fact">
                  <dt>{{ fact.label }}</dt>
                  <dd :class="fact.valueClass">{{ fact.value }}</dd>
                  <dd v-if="fact.note" class="accounts-fact__note">{{ fact.note }}</dd>
                </div>
              </dl>
              <router-link v-if="focus.link" :to="focus.link.to" class="accounts-link">
                {{ focus.link.label }}
              </router-link>
            </Card>

            <Card
              class="accounts-card accounts-card--secondary space-y-4 rounded-2xl p-5 shadow-xl"
            >
              <header>
                <h2 class="accounts-subpanel-title">Balance History</h2>
                <p class="text-sm text-muted">{{ periodDates.start }} – {{ periodDates.end }}</p>
              </header>

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

            <Card
              class="accounts-card accounts-card--secondary space-y-4 rounded-2xl p-5 shadow-xl"
            >
              <header>
                <h2 class="accounts-subpanel-title">Money movement in selected period</h2>
                <p class="text-sm text-muted">
                  Posted transactions {{ periodDates.start }} – {{ periodDates.end }}. Card payments
                  and transfers count as movement, and pending items are not included.
                </p>
              </header>

              <SkeletonCard v-if="loadingSummary" />
              <RetryError
                v-else-if="summaryError"
                message="Failed to load summary"
                @retry="retrySummary"
              />

              <template v-else>
                <div class="grid gap-3 md:grid-cols-3">
                  <article
                    v-for="stat in netSummaryStats"
                    :key="stat.key"
                    class="accounts-kpi-card rounded-xl p-3"
                  >
                    <p class="text-xs uppercase text-muted">{{ stat.label }}</p>
                    <p class="mt-2 text-2xl font-bold" :class="stat.valueClass">
                      {{ stat.value }}
                    </p>
                  </article>
                </div>
                <p
                  v-if="balanceChangeLabel"
                  class="text-xs text-muted"
                  data-testid="balance-change"
                >
                  Balance change over the period: {{ balanceChangeLabel }} (differs from movement
                  when balances move without matching transactions).
                </p>
              </template>
            </Card>

            <Card
              class="accounts-card accounts-card--secondary space-y-4 rounded-2xl p-5 shadow-xl"
            >
              <header class="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 class="accounts-subpanel-title">Latest transactions</h2>
                  <p class="text-sm text-muted" data-testid="recent-transactions-caption">
                    {{ recentTransactionsCaption }}
                  </p>
                </div>
                <router-link
                  :to="{ path: '/transactions', query: { account_id: String(accountId) } }"
                  class="accounts-link"
                  data-testid="view-account-transactions"
                >
                  View all in Transactions
                </router-link>
              </header>

              <SkeletonCard v-if="loadingTransactions" />
              <RetryError
                v-else-if="transactionsError"
                message="Failed to load transactions"
                @retry="retryTransactions"
              />
              <p v-else-if="!recentTransactions.length" class="text-sm text-muted">
                No transactions in this period.
              </p>
              <TransactionsTable v-else :transactions="recentTransactions" />
            </Card>
          </template>

          <Card class="accounts-card accounts-card--tertiary space-y-6 rounded-2xl p-6 shadow-xl">
            <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 class="accounts-subpanel-title">Most Active Accounts</h3>
                <p class="text-sm text-muted">
                  All posted transactions {{ periodDates.start }} – {{ periodDates.end }}
                  (pending excluded; internal transfers included).
                </p>
              </div>

              <select
                v-model="activityMode"
                class="input w-full sm:w-72"
                :disabled="loadingActivityBreakdown || !accountActivityBreakdown.length"
              >
                <option value="count">Most active by transaction count</option>
                <option value="value">Most active by total transaction value</option>
              </select>
            </header>

            <SkeletonCard v-if="loadingActivityBreakdown" />
            <RetryError
              v-else-if="activityBreakdownError"
              message="Failed to load account activity"
              @retry="loadActivityBreakdown"
            />

            <div v-else-if="mostActiveAccounts.length" class="accounts-activity-list">
              <article
                v-for="(row, index) in mostActiveAccounts"
                :key="row.accountId"
                class="accounts-activity-item rounded-xl p-4"
              >
                <div class="flex items-center justify-between gap-3">
                  <p class="text-sm font-semibold text-[var(--theme-fg)]">
                    {{ index + 1 }}. {{ row.name }}
                  </p>
                  <span class="accounts-activity-score text-xs font-semibold">{{
                    row.primaryMetricLabel
                  }}</span>
                </div>
                <div class="mt-3 grid gap-2 text-xs text-muted sm:grid-cols-2">
                  <p>
                    Transaction count:
                    <span class="text-[var(--theme-fg)]">{{ row.transactionCount }}</span>
                  </p>
                  <p>
                    Total transaction value:
                    <span class="text-[var(--theme-fg)]">{{ row.totalValueLabel }}</span>
                  </p>
                </div>
              </article>
            </div>
            <p v-else class="text-sm text-muted">
              No activity data is available for the selected range.
            </p>
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
      <section class="accounts-tab-panel">
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

    <!-- CONNECTIONS TAB -->
    <template #Connections>
      <section class="accounts-tab-panel">
        <Card class="accounts-card accounts-card--tertiary space-y-6 rounded-2xl p-6 shadow-xl">
          <h2 class="accounts-panel-title">Connections</h2>
          <LinkedAccountsSection
            :accounts="linkedAccounts"
            :use-demo-fallback="false"
            :enable-promotion-editor="false"
            :reconnecting-id="reconnectingId"
            :connection-messages="reconnectMessage"
            @add-promotion="handleAddPromotion"
            @reconnect="reconnectConnection"
          />
        </Card>
      </section>
    </template>

    <template #sidebar>
      <AccountActionsSidebar />
    </template>
  </TabbedPageLayout>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useToast } from 'vue-toastification'
import { useRoute } from 'vue-router'
import { Wallet } from 'lucide-vue-next'

import api from '@/services/api'
import { fetchAccountActivityBreakdown, fetchNetChanges, rangeToDates } from '@/api/accounts'
import { fetchTransactions } from '@/api/transactions'
import { useAccountHistory } from '@/composables/useAccountHistory'
import { useRefreshNotification } from '@/composables/useRefreshNotification'
import { usePlaidReconnect } from '@/composables/usePlaidReconnect'
import { uniqueReconnectConnections } from '@/utils/plaidConnectionStatus'

import { formatAmount } from '@/utils/format'
import {
  accountUtilization,
  amountOwed,
  aprInfo,
  classifyAccount,
  creditLimit,
  syncStatus,
} from '@/utils/accountPortfolio'
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
import AccountPortfolioOverview from '@/components/accounts/AccountPortfolioOverview.vue'
import AccountPortfolioList from '@/components/accounts/AccountPortfolioList.vue'
import AccountActionsSidebar from '@/components/forms/AccountActionsSidebar.vue'

const route = useRoute()
const toast = useToast()
const { notifyRefreshStarted, notifyRefreshSuccess, notifyRefreshError } = useRefreshNotification()

const accounts = ref([])
const reconnectingId = ref(null)
const reconnectMessage = ref({})
const { reconnect } = usePlaidReconnect()
const accountsLoading = ref(false)
const accountId = ref(route.query.accountId?.toString() || null)

const netSummary = ref({ income: 0, expense: 0, net: 0, balanceChange: null })
const recentTransactions = ref([])

const ranges = ['7d', '30d', '90d', '180d', 'ytd', '365d']
const rangeLabels = {
  '7d': 'Last 7 days',
  '30d': 'Last 30 days',
  '90d': 'Last 90 days',
  '180d': 'Last 180 days',
  ytd: 'Year to date',
  '365d': 'Last 365 days',
}
const selectedRange = ref('30d')
const activityMode = ref('count')

const {
  history: accountHistory,
  loading: loadingHistory,
  error: historyError,
  loadHistory,
} = useAccountHistory(accountId, selectedRange)

const loadingSummary = ref(false)
const loadingTransactions = ref(false)
const loadingActivityBreakdown = ref(false)

const summaryError = ref(null)
const transactionsError = ref(null)
const activityBreakdownError = ref(null)
const accountActivityBreakdown = ref([])
const accountsError = ref(null)
const recentTransactionsTotal = ref(null)
let loadDataToken = 0
let activityToken = 0

const activeTab = ref('Summary')

const DEFAULT_PORTFOLIO_FILTERS = {
  query: '',
  group: 'all',
  institution: 'all',
  connection: 'all',
  sort: 'name',
  includeHidden: false,
}
const portfolioFilters = ref({ ...DEFAULT_PORTFOLIO_FILTERS })
const detailsRef = ref(null)

function setPortfolioGroup(group) {
  portfolioFilters.value = {
    ...portfolioFilters.value,
    group: portfolioFilters.value.group === group ? 'all' : group,
  }
}

function resetPortfolioFilters() {
  portfolioFilters.value = { ...DEFAULT_PORTFOLIO_FILTERS }
}

/** Select an account from the ledger without leaving the all-accounts context. */
async function selectAccount(id) {
  accountId.value = id ? String(id) : null
  activeTab.value = 'Summary'
  await nextTick()
  detailsRef.value?.scrollIntoView?.({ behavior: 'smooth', block: 'start' })
}

function clearSelectedAccount() {
  accountId.value = null
}

const hasAccounts = computed(() => accounts.value.length > 0)
const linkedAccounts = computed(() =>
  accounts.value.map((account) => ({
    id: String(account.account_id),
    account_id: account.account_id,
    institution_name: account.institution_name,
    name: account.display_name || account.name || 'Unnamed account',
    institution: account.institution_name || account.institution || 'Unknown Institution',
    type: account.type || account.account_type || 'Other',
    subtype: account.subtype || account.account_subtype || '',
    mask: account.mask || '',
    apr: account.apr,
    connection_status: account.connection_status,
    balance: account.current_balance ?? account.balance,
    limit: account.limit,
    status: account.status,
    promotions: account.promotions || [],
  })),
)
const canFetchAccountData = computed(() => hasAccounts.value && Boolean(accountId.value))

const tabs = computed(() => [
  { label: 'Overview', slot: 'Summary' },
  { label: 'Activity', slot: 'Transactions', disabled: !canFetchAccountData.value },
  { label: 'Trends', slot: 'Charts', disabled: !canFetchAccountData.value },
  { label: 'Connections', slot: 'Connections' },
])

const selectedAccount = computed(
  () =>
    accounts.value.find((account) => String(account.account_id) === String(accountId.value)) ||
    null,
)
const attentionConnectionCount = computed(() => uniqueReconnectConnections(accounts.value).length)
const selectedAccountStatus = computed(() => {
  const account = selectedAccount.value
  if (!account) return null
  const balance = account.current_balance ?? account.balance
  return {
    name: account.display_name || account.name || 'Unnamed account',
    detail: [account.institution_name, account.mask ? `•••• ${account.mask}` : '']
      .filter(Boolean)
      .join(' '),
    balance: balance == null ? '' : formatAmount(balance),
    connection: account.connection_status?.requires_reauth ? 'Needs reconnect' : 'Connected',
  }
})

const periodDates = computed(() => rangeToDates(selectedRange.value))

const netSummaryStats = computed(() => [
  {
    key: 'income',
    label: 'Money in',
    value: formatAmount(netSummary.value.income),
    valueClass: 'text-green-500',
  },
  {
    key: 'expense',
    label: 'Money out',
    value: formatAmount(netSummary.value.expense),
    valueClass: 'text-red-500',
  },
  {
    key: 'net',
    label: 'Net movement',
    value: formatAmount(netSummary.value.net),
    valueClass: 'text-yellow-500',
  },
])

const balanceChangeLabel = computed(() =>
  netSummary.value.balanceChange == null ? '' : formatAmount(netSummary.value.balanceChange),
)

const recentTransactionsCaption = computed(() => {
  const shown = recentTransactions.value.length
  const total = recentTransactionsTotal.value
  const range = `${periodDates.value.start} – ${periodDates.value.end}`
  return total != null && total > shown
    ? `Showing ${shown} of ${total} in ${range}`
    : `${shown} in ${range}`
})

/** Facts for the selected account, tailored to its type; unknown stays "Not reported". */
const focus = computed(() => {
  const account = selectedAccount.value
  if (!account) return { identity: '', facts: [], link: null }
  const group = classifyAccount(account)
  const fact = (label, value, extra = {}) => ({ label, value, ...extra })
  const money = (value) => (value == null ? 'Not reported' : formatAmount(value))
  const facts = []
  let link = null

  const balance = account.current_balance ?? account.balance
  if (group === 'credit' || group === 'loan') {
    const owed = amountOwed(account)
    facts.push(fact('Amount owed', owed == null ? 'Unknown' : formatAmount(owed)))
  } else {
    facts.push(
      fact(
        group === 'investment' ? 'Value' : 'Current balance',
        money(balance == null ? null : balance),
      ),
    )
  }

  if (group === 'depository') {
    facts.push(
      fact('Available', money(account.available_balance), {
        note: account.available_balance == null ? '' : 'As reported by the institution',
      }),
    )
  }

  if (group === 'credit') {
    const limit = creditLimit(account)
    const util = accountUtilization(account)
    facts.push(fact('Credit limit', limit == null ? 'Unknown' : formatAmount(limit)))
    facts.push(
      fact(
        'Utilization',
        util ? `${util.percent}%${util.overlimit ? ' (over limit)' : ''}` : 'N/A (limit unknown)',
      ),
    )
    if (account.available_balance != null) {
      facts.push(
        fact('Available credit', formatAmount(account.available_balance), {
          note: 'Reported by the issuer',
        }),
      )
    } else if (limit != null && amountOwed(account) != null) {
      facts.push(
        fact('Remaining credit', formatAmount(Math.max(limit - amountOwed(account), 0)), {
          note: 'Calculated from limit and balance, not issuer-reported',
        }),
      )
    }
  }

  if (group === 'credit' || group === 'loan') {
    const apr = aprInfo(account)
    const breakdown = account.interest_rate_breakdown || {}
    const loanRate = breakdown.loan_interest_rate?.percentage
    const buckets = Object.entries(breakdown)
      .filter(([key]) => key !== 'loan_interest_rate')
      .map(
        ([key, entries]) =>
          `${key.replace(/_/g, ' ')} ${(entries || []).map((e) => `${e.apr_percentage}%`).join(', ')}`,
      )
    if (group === 'loan' && loanRate != null) {
      facts.push(fact('Interest rate', `${loanRate}%`, { note: 'Reported by the provider' }))
    } else {
      facts.push(
        fact('APR', apr.value == null ? 'Unknown' : `${apr.value}%`, {
          note: buckets.length
            ? `${apr.label} · ${buckets.join(' · ')}`
            : apr.label || 'No verified rate',
        }),
      )
    }
    if (group === 'credit' && account.interest_paid_recent) {
      facts.push(
        fact('Interest charged', formatAmount(account.interest_paid_recent.total), {
          note: `Last ${account.interest_paid_recent.window_days} days, from posted transactions`,
        }),
      )
    }
    if (account.minimum_payment_amount != null) {
      facts.push(fact('Minimum payment', formatAmount(account.minimum_payment_amount)))
    }
    if (account.next_payment_due_date) {
      facts.push(fact('Next payment due', account.next_payment_due_date))
    }
    if (account.statement_balance != null) {
      facts.push(fact('Statement balance', formatAmount(account.statement_balance)))
    }
  }

  if (group === 'investment') {
    link = { to: '/investments', label: 'Open Investments' }
  }

  const connection = account.connection_status?.requires_reauth ? 'Needs reconnect' : 'Connected'
  const identity = [
    account.institution_name,
    account.subtype || account.type,
    account.mask ? `•••• ${account.mask}` : '',
    syncStatus(account),
    connection,
  ]
    .filter(Boolean)
    .join(' · ')
  return { identity, facts, link }
})

const mostActiveAccounts = computed(() => {
  const metric = activityMode.value === 'value' ? 'totalValue' : 'transactionCount'
  return [...accountActivityBreakdown.value]
    .sort((left, right) => right[metric] - left[metric])
    .slice(0, 5)
    .map((row) => ({
      ...row,
      totalValueLabel: formatAmount(row.totalValue),
      primaryMetricLabel:
        metric === 'totalValue'
          ? `${formatAmount(row.totalValue)} total value`
          : `${row.transactionCount} transactions`,
    }))
})

function handleAccountSelection(e) {
  accountId.value = e.target.value || null
}

async function loadAccounts() {
  accountsLoading.value = true
  accountsError.value = null
  try {
    const resp = await api.getAccounts({ include_hidden: true })
    accounts.value = resp?.accounts || []
  } catch (error) {
    accountsError.value = error
  } finally {
    accountsLoading.value = false
  }
}

async function retryAccounts() {
  await loadAccounts()
  if (!accountsError.value) await Promise.all([loadData(), loadActivityBreakdown()])
}

async function reconnectConnection(connection) {
  const id = connection.connectionId
  const key = connection.key ?? `connection:${String(id)}`
  const setMessage = (message) => {
    reconnectMessage.value = { ...reconnectMessage.value, [key]: message }
  }
  reconnectingId.value = key
  setMessage('')
  const accountIds = connection.accountIds ?? connection.accounts.map((a) => a.account_id)
  try {
    const result = await reconnect({
      connectionId: id,
      accountId: connection.accountId ?? accountIds[0],
      accountCount: accountIds.length,
      onSuccess: async () => {
        setMessage('Verifying connection…')
        // Refresh every account in the Item, then trust persisted health, not Link success.
        await api.refreshAccounts({ account_ids: accountIds })
        await loadAccounts()
        setMessage(
          uniqueReconnectConnections(accounts.value).some((item) => item.key === key)
            ? 'Plaid still reports that this connection needs attention.'
            : '',
        )
      },
      onError: setMessage,
    })
    if (result.status === 'busy') setMessage(result.message)
    else if (result.status === 'cancelled') setMessage('')
  } finally {
    reconnectingId.value = null
  }
}

/**
 * Load per-account activity for the selected period with one grouped request (no row cap).
 * Stale responses from a superseded period are ignored.
 * @returns {Promise<void>}
 */
async function loadActivityBreakdown() {
  if (!hasAccounts.value) {
    accountActivityBreakdown.value = []
    return
  }

  const token = ++activityToken
  const { start, end } = rangeToDates(selectedRange.value)
  loadingActivityBreakdown.value = true
  activityBreakdownError.value = null

  try {
    const response = await fetchAccountActivityBreakdown({ start_date: start, end_date: end })
    if (token !== activityToken) return
    const byId = new Map(accounts.value.map((account) => [String(account.account_id), account]))
    accountActivityBreakdown.value = (response?.accounts ?? [])
      .map((row) => ({
        accountId: row.account_id,
        name: byId.get(String(row.account_id))?.display_name || row.name || 'Unnamed account',
        transactionCount: Number(row.transaction_count ?? 0),
        totalValue: Number(row.transaction_value_abs ?? 0),
      }))
      .filter((row) => row.transactionCount > 0 || row.totalValue > 0)
  } catch (error) {
    if (token !== activityToken) return
    activityBreakdownError.value = error
  } finally {
    if (token === activityToken) loadingActivityBreakdown.value = false
  }
}

/**
 * Load the selected account's period data. Sections fail independently and a newer
 * selection or period supersedes any in-flight response.
 * @returns {Promise<boolean>} True when every section loaded.
 */
async function loadData() {
  if (!canFetchAccountData.value) return false

  const token = ++loadDataToken
  const id = accountId.value
  const { start, end } = rangeToDates(selectedRange.value)

  loadingSummary.value = true
  loadingTransactions.value = true
  summaryError.value = null
  transactionsError.value = null

  const [summary, transactions, history] = await Promise.allSettled([
    fetchNetChanges(id, { start_date: start, end_date: end }),
    fetchTransactions({
      account_ids: [id],
      start_date: start,
      end_date: end,
      page: 1,
      page_size: 10,
    }),
    loadHistory(),
  ])
  if (token !== loadDataToken) return false

  if (summary.status === 'fulfilled') {
    const summaryData = summary.value?.data ?? summary.value ?? {}
    netSummary.value = {
      income: Number(summaryData?.money_in ?? summaryData?.income ?? 0),
      expense: Number(summaryData?.money_out ?? summaryData?.expense ?? 0),
      net: Number(summaryData?.net_movement ?? summaryData?.net ?? 0),
      balanceChange:
        summaryData?.balance_change == null ? null : Number(summaryData.balance_change),
    }
  } else {
    summaryError.value = summary.reason
  }

  if (transactions.status === 'fulfilled') {
    recentTransactions.value = transactions.value?.transactions ?? []
    recentTransactionsTotal.value = transactions.value?.total ?? null
  } else {
    transactionsError.value = transactions.reason
  }

  loadingSummary.value = false
  loadingTransactions.value = false
  return (
    summary.status === 'fulfilled' &&
    transactions.status === 'fulfilled' &&
    history.status === 'fulfilled'
  )
}

async function refreshSelectedAccountData() {
  notifyRefreshStarted('Refreshing account data…')
  const didSucceed = await loadData()
  if (didSucceed) {
    notifyRefreshSuccess('Account data refreshed.')
    return
  }
  notifyRefreshError('Unable to refresh account data.')
}

function retrySummary() {
  loadData()
}

function retryHistory() {
  loadHistory()
}

function retryTransactions() {
  loadData()
}

function handleAddPromotion() {
  toast.error('Promotion persistence is not available yet. Changes remain local drafts.')
}

onMounted(async () => {
  await loadAccounts()
  await Promise.all([loadData(), loadActivityBreakdown()])
})

watch(accountId, loadData)
watch(selectedRange, () => {
  loadData()
  loadActivityBreakdown()
})
</script>
<style scoped>
.accounts-context {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.accounts-context__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.accounts-context__status {
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.accounts-context__attention {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
}

.accounts-tab-panel {
  margin-top: var(--space-8, 2rem);
  display: flex;
  flex-direction: column;
  gap: var(--space-8, 2rem);
}

.accounts-panel-title {
  font-size: var(--font-size-4xl, 2rem);
  font-weight: var(--font-weight-bold, 700);
  line-height: var(--line-height-tight, 1.2);
  color: var(--theme-fg);
}

.accounts-subpanel-title {
  font-size: var(--font-size-2xl, 1.5rem);
  font-weight: var(--font-weight-semibold, 600);
  line-height: var(--line-height-snug, 1.3);
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

.accounts-period-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem;
}

.accounts-period-bar__label {
  font-size: 0.85rem;
  font-weight: 600;
}

.accounts-period-bar__dates {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.accounts-facts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 11rem), 1fr));
  gap: 0.75rem 1.25rem;
  margin: 0;
}

.accounts-fact dt {
  font-size: 0.72rem;
  color: var(--color-text-muted);
}

.accounts-fact dd {
  margin: 0.1rem 0 0;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.accounts-fact dd.accounts-fact__note {
  font-size: 0.72rem;
  font-weight: 400;
  color: var(--color-text-muted);
}

.accounts-link {
  font-size: 0.85rem;
  color: var(--color-accent-cyan);
  text-decoration: underline;
}

.accounts-details-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  scroll-margin-top: 1rem;
}

.accounts-kpi-card {
  border: 1px solid var(--themed-border);
  background: var(--table-surface);
}

.accounts-activity-list {
  display: grid;
  gap: var(--space-3, 0.75rem);
}

.accounts-activity-item {
  border: 1px solid var(--table-border);
  background: var(--table-surface);
}

.accounts-activity-score {
  color: color-mix(in srgb, var(--color-accent-indigo) 70%, var(--theme-fg));
}

@media (max-width: 768px) {
  .accounts-panel-title {
    font-size: var(--font-size-3xl, 1.875rem);
  }

  .accounts-subpanel-title {
    font-size: var(--font-size-xl, 1.25rem);
  }
}
</style>
