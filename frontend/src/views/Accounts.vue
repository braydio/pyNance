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

          <header
            v-if="selectedAccount"
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
            v-if="selectedAccount"
            class="accounts-card accounts-card--secondary space-y-6 rounded-2xl p-6 shadow-xl"
          >
            <header class="flex justify-between items-center">
              <div>
                <h2 class="accounts-subpanel-title">Net Change Summary</h2>
                <p class="text-sm text-muted">Performance for the selected date range.</p>
              </div>
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

          <Card
            v-if="selectedAccount"
            class="accounts-card accounts-card--secondary space-y-6 rounded-2xl p-6 shadow-xl"
          >
            <div class="flex items-center justify-between">
              <h2 class="accounts-subpanel-title">Balance History</h2>

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
            <header class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 class="accounts-subpanel-title">Most Active Accounts</h3>
                <p class="text-sm text-muted">
                  Ranked by recent transaction activity in the selected date range.
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
import { fetchNetChanges, fetchRecentTransactions, rangeToDates } from '@/api/accounts'
import { useAccountHistory } from '@/composables/useAccountHistory'
import { useRefreshNotification } from '@/composables/useRefreshNotification'
import { usePlaidReconnect } from '@/composables/usePlaidReconnect'
import { uniqueReconnectConnections } from '@/utils/plaidConnectionStatus'

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

const netSummary = ref({ income: 0, expense: 0, net: 0 })
const recentTransactions = ref([])

const ranges = ['7d', '30d', '90d', '365d']
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

/**
 * Resolves a numeric amount from supported transaction response fields.
 * @param {Record<string, any>} transaction
 * @returns {number}
 */
function transactionAmount(transaction) {
  const raw = transaction?.amount ?? transaction?.signed_amount ?? transaction?.value ?? 0
  const normalized = Number(raw)
  return Number.isFinite(normalized) ? normalized : 0
}

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
  try {
    const resp = await api.getAccounts({ include_hidden: true })
    accounts.value = resp?.accounts || []
  } finally {
    accountsLoading.value = false
  }
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
 * Loads account-level transaction activity and computes breakdown metrics for ranking.
 * @returns {Promise<void>}
 */
async function loadActivityBreakdown() {
  if (!hasAccounts.value) {
    accountActivityBreakdown.value = []
    return
  }

  loadingActivityBreakdown.value = true
  activityBreakdownError.value = null

  try {
    const results = await Promise.allSettled(
      accounts.value.map(async (account) => {
        const response = await fetchRecentTransactions(account.account_id, 100)
        const transactions = response?.transactions ?? []
        return {
          accountId: account.account_id,
          name: account.display_name || account.name || 'Unnamed account',
          transactionCount: transactions.length,
          totalValue: transactions.reduce((sum, tx) => sum + Math.abs(transactionAmount(tx)), 0),
        }
      }),
    )

    accountActivityBreakdown.value = results
      .filter((result) => result.status === 'fulfilled')
      .map((result) => result.value)
      .filter((row) => row.transactionCount > 0 || row.totalValue > 0)
  } catch (error) {
    activityBreakdownError.value = error
  } finally {
    loadingActivityBreakdown.value = false
  }
}

async function loadData() {
  if (!canFetchAccountData.value) return false

  const { start, end } = rangeToDates(selectedRange.value)

  loadingSummary.value = true
  loadingTransactions.value = true
  summaryError.value = null
  transactionsError.value = null

  try {
    const [summary, transactions] = await Promise.all([
      fetchNetChanges(accountId.value, { start_date: start, end_date: end }),
      fetchRecentTransactions(accountId.value, 10),
      loadHistory(),
    ])

    const summaryData = summary?.data ?? summary ?? {}

    netSummary.value = {
      income: Number(summaryData?.income ?? 0),
      expense: Number(summaryData?.expense ?? 0),
      net: Number(summaryData?.net ?? 0),
    }

    recentTransactions.value = transactions?.transactions ?? []
    return true
  } catch (err) {
    summaryError.value = err
    transactionsError.value = err
    return false
  } finally {
    loadingSummary.value = false
    loadingTransactions.value = false
  }
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
watch(selectedRange, loadData)
watch(selectedRange, loadActivityBreakdown)
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
