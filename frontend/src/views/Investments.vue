<!-- Investments.vue - Skeleton layout for the future Investments dashboard. -->
<template>
  <BasePageLayout class="investments-view" gap="gap-8">
    <PageHeader :icon="TrendingUp">
      <template #title> Investments </template>
      <template #subtitle> Monitor performance across your linked investment accounts </template>
    </PageHeader>

    <nav class="section-subnav" aria-label="Investments page navigation">
      <button
        v-for="item in sectionNavItems"
        :key="item.key"
        type="button"
        :aria-controls="item.target"
        :aria-current="activeSection === item.key ? 'true' : undefined"
        :class="['section-subnav__link', { 'is-active': activeSection === item.key }]"
        @click="scrollToSection(item.key)"
      >
        {{ item.label }}
      </button>
    </nav>

    <section
      id="portfolio-overview"
      ref="overviewSection"
      tabindex="-1"
      class="surface-primary p-4 md:p-5"
    >
      <h2 class="text-xl font-semibold mb-3">Portfolio</h2>
      <div v-if="loading" class="text-muted">Loading…</div>
      <div v-else class="overview-grid" data-testid="portfolio-summary">
        <div class="metric metric--lead">
          <span class="k">Total value</span
          ><span class="v">{{ formatCurrency(portfolioTotal) }}</span>
        </div>
        <div class="metric">
          <span class="k">Accounts</span><span class="v">{{ accounts.length }}</span>
        </div>
        <div class="metric">
          <span class="k">Holdings</span><span class="v">{{ holdings.length }}</span>
        </div>
        <div class="metric">
          <span class="k">Securities</span><span class="v">{{ uniqueSecurityCount }}</span>
        </div>
      </div>
    </section>

    <section id="holdings" ref="holdingsSection" tabindex="-1">
      <h2 class="text-xl font-semibold mb-2">Holdings</h2>
      <div class="filters">
        <label>
          <span>Institution</span>
          <select v-model="selectedInstitution" class="input select">
            <option value="">All</option>
            <option v-for="inst in institutions" :key="inst" :value="inst">{{ inst }}</option>
          </select>
        </label>
        <label>
          <span>Account</span>
          <select v-model="selectedAccount" class="input select">
            <option value="">All</option>
            <option
              v-for="acc in accountsForInstitution"
              :key="acc.account_id"
              :value="acc.account_id"
            >
              {{ accDisplay(acc) }}
            </option>
          </select>
        </label>
      </div>
      <div v-if="loading" class="text-muted">Loading holdings…</div>
      <div v-else-if="filteredHoldings.length === 0" class="text-muted">No holdings yet.</div>
      <div v-else class="holdings-table" role="region" aria-label="Holdings" tabindex="0">
        <div class="totals-bar" data-testid="holdings-summary">
          <div>
            Filtered holdings value: <strong>{{ formatCurrency(filteredTotal) }}</strong>
            <span class="muted" data-testid="holdings-summary-scope">
              · {{ filteredHoldings.length }} holding{{
                filteredHoldings.length === 1 ? '' : 's'
              }}
              in {{ filteredAccountIds.length }} account{{
                filteredAccountIds.length === 1 ? '' : 's'
              }}
            </span>
          </div>
          <div class="muted" data-testid="holdings-summary-entire">
            Entire connected holdings value: {{ formatCurrency(portfolioTotal) }}
            <template v-if="isFilteredHoldings">
              · {{ holdings.length }} holdings in {{ accounts.length }} accounts
            </template>
          </div>
        </div>
        <template v-if="showAggregateHoldings">
          <div class="thead holdings-summary-head">
            <div>Account</div>
            <div>Institution</div>
            <div class="num">Holdings</div>
            <div class="num">Securities</div>
            <div class="num">Total Value</div>
            <div class="expand-cell">Details</div>
          </div>
          <template v-for="summary in summarizedHoldings" :key="summary.account_id">
            <button
              type="button"
              class="trow holdings-summary-row"
              :aria-expanded="
                expandedHoldingAccounts.includes(summary.account_id) ? 'true' : 'false'
              "
              :aria-controls="`holdings-panel-${summary.account_id}`"
              :data-testid="`holding-toggle-${summary.account_id}`"
              @click="toggleHoldingAccount(summary.account_id)"
            >
              <div class="account-cell">
                {{ accountLabelById[summary.account_id] || summary.account_id }}
              </div>
              <div>{{ summary.institution_name || '—' }}</div>
              <div class="num">
                {{ summary.holdings_count }}
              </div>
              <div class="num">
                {{ summary.securities_count }}
              </div>
              <div class="num">
                {{ formatCurrency(summary.total_value) }}
              </div>
              <div class="expand-cell">
                {{ expandedHoldingAccounts.includes(summary.account_id) ? 'Hide' : 'Show' }}
              </div>
            </button>
            <div
              v-if="expandedHoldingAccounts.includes(summary.account_id)"
              :id="`holdings-panel-${summary.account_id}`"
              class="holdings-details-panel"
            >
              <div class="holdings-details-head">
                <div>Ticker</div>
                <div>Name</div>
                <div class="num">Qty</div>
                <div class="num">Price</div>
                <div class="num">Value</div>
              </div>
              <div
                v-for="holding in summary.holdings"
                :key="holding.account_id + ':' + holding.security_id"
                class="holdings-details-row"
              >
                <div>{{ holding.security?.ticker_symbol || '—' }}</div>
                <div class="name-clip" :title="holding.security?.name || holding.security_id">
                  {{ holding.security?.name || holding.security_id }}
                </div>
                <div class="num">
                  {{ formatNum(holding.quantity) }}
                </div>
                <div class="num">
                  {{ formatCurrency(holding.security?.price) }}
                </div>
                <div class="num">
                  {{ formatCurrency(holdingValue(holding)) }}
                </div>
              </div>
            </div>
          </template>
        </template>
        <template v-else>
          <div class="thead">
            <div>Account</div>
            <div>Ticker</div>
            <div>Name</div>
            <div class="num">Qty</div>
            <div class="num">Price</div>
            <div class="num">Value</div>
          </div>
          <div v-for="h in filteredHoldings" :key="h.account_id + ':' + h.security_id" class="trow">
            <div>{{ accountLabelById[h.account_id] || h.account_id }}</div>
            <div>{{ h.security?.ticker_symbol || '—' }}</div>
            <div class="name-clip" :title="h.security?.name || h.security_id">
              {{ h.security?.name || h.security_id }}
            </div>
            <div class="num">
              {{ formatNum(h.quantity) }}
            </div>
            <div class="num">
              {{ formatCurrency(h.security?.price) }}
            </div>
            <div class="num">
              {{ formatCurrency(holdingValue(h)) }}
            </div>
          </div>
        </template>
      </div>
      <div v-if="showAggregateHoldings" class="text-muted holdings-note">
        Multiple accounts are selected. Expand an account to inspect individual holdings.
      </div>
      <div
        v-if="Object.keys(totalsByInstitution).length > 1"
        class="inst-summary"
        data-testid="inst-summary"
      >
        <div class="muted">Subtotal by institution (filtered holdings)</div>
        <div v-for="(val, inst) in totalsByInstitution" :key="inst" class="inst-row">
          <span class="inst">{{ inst }}</span>
          <span class="val">{{ formatCurrency(val) }}</span>
        </div>
      </div>
    </section>

    <section id="performance" ref="performanceSection" tabindex="-1">
      <h2 class="text-xl font-semibold mb-2">Performance</h2>
      <div class="perf-grid">
        <PortfolioAllocationChart :allocations="allocationByType" />
      </div>
    </section>

    <section id="investment-transactions" ref="transactionsSection" tabindex="-1">
      <h2 class="text-xl font-semibold mb-2">Recent Investment Transactions</h2>
      <details class="filters-disclosure" data-testid="tx-filters-disclosure">
        <summary>
          Filters<span
            v-if="activeTxFilterCount"
            data-testid="tx-filter-count"
            :title="`${activeTxFilterCount} active ${activeTxFilterCount === 1 ? 'filter' : 'filters'}`"
          >
            ({{ activeTxFilterCount }})</span
          >
        </summary>
        <div class="filters filters--grid">
          <label>
            <span>Account</span>
            <select v-model="txAccountId" class="input select" data-testid="tx-filter-account">
              <option value="">All</option>
              <option v-for="acc in accounts" :key="acc.account_id" :value="acc.account_id">
                {{ accDisplay(acc) }}
              </option>
            </select>
          </label>
          <label>
            <span>Security ID</span>
            <input
              v-model="txSecurityId"
              class="input"
              data-testid="tx-filter-security-id"
              type="text"
            />
          </label>
          <label>
            <span>Type</span>
            <input v-model="txType" class="input" data-testid="tx-filter-type" type="text" />
          </label>
          <label>
            <span>Subtype</span>
            <input v-model="txSubtype" class="input" data-testid="tx-filter-subtype" type="text" />
          </label>
          <label>
            <span>Start Date</span>
            <input
              v-model="txStartDate"
              class="input"
              data-testid="tx-filter-start-date"
              type="date"
            />
          </label>
          <label>
            <span>End Date</span>
            <input v-model="txEndDate" class="input" data-testid="tx-filter-end-date" type="date" />
          </label>
          <button
            type="button"
            class="btn btn-outline"
            :disabled="!activeTxFilterCount"
            data-testid="tx-filter-reset"
            @click="resetTxFilters"
          >
            Reset filters
          </button>
        </div>
      </details>
      <div v-if="txLoading" class="text-muted">Loading transactions…</div>
      <div v-else>
        <div v-if="txData.length === 0" class="text-muted">No transactions found.</div>
        <template v-else>
          <div class="tx-activity" data-testid="tx-activity">
            <span class="muted" data-testid="tx-activity-scope">
              This page only · {{ txData.length }} transaction{{
                txData.length === 1 ? '' : 's'
              }}
              (page {{ txPage }} of {{ txTotalPages }}); not an all-matching total
            </span>
            <ul class="tx-activity__groups">
              <li
                v-for="group in txActivityGroups"
                :key="group.key"
                :data-testid="`tx-activity-${group.key}`"
              >
                {{ group.label }} · {{ group.count }} · {{ formatCurrency(group.amount) }}
              </li>
            </ul>
          </div>
          <div
            class="tx-table"
            role="table"
            aria-label="Investment transactions, current page"
            tabindex="0"
          >
            <div class="thead" role="row">
              <div role="columnheader">Date</div>
              <div role="columnheader">Account</div>
              <div role="columnheader">Security</div>
              <div role="columnheader">Name</div>
              <div class="num" role="columnheader">Qty</div>
              <div class="num" role="columnheader">Price</div>
              <div class="num" role="columnheader">Amount</div>
            </div>
            <div v-for="tx in txData" :key="tx.investment_transaction_id" class="trow" role="row">
              <div role="cell">{{ (tx.date || '').slice(0, 10) }}</div>
              <div role="cell">{{ accountLabelById[tx.account_id] || tx.account_id }}</div>
              <div role="cell">{{ tx.security_id || '—' }}</div>
              <div class="name-clip" role="cell">
                {{ tx.name || tx.subtype || tx.type }}
              </div>
              <div class="num" role="cell">{{ formatNum(tx.quantity) }}</div>
              <div class="num" role="cell">{{ formatCurrency(tx.price) }}</div>
              <div class="num" role="cell">{{ formatCurrency(tx.amount) }}</div>
            </div>
          </div>
          <div class="pager">
            <button
              type="button"
              class="btn"
              :disabled="txPage === 1"
              @click="loadTransactions(txPage - 1)"
            >
              Prev
            </button>
            <span>Page {{ txPage }} of {{ txTotalPages }}</span>
            <button
              type="button"
              class="btn"
              :disabled="txPage === txTotalPages"
              @click="loadTransactions(txPage + 1)"
            >
              Next
            </button>
          </div>
        </template>
      </div>
    </section>
    <section
      id="maintenance"
      ref="maintenanceSection"
      tabindex="-1"
      class="surface-quiet p-4 md:p-5"
    >
      <h2 class="text-lg font-semibold mb-2">Manage investment connections</h2>
      <div class="controls">
        <label>
          <span>Start</span>
          <input v-model="startDate" class="input" type="date" />
        </label>
        <label>
          <span>End</span>
          <input v-model="endDate" class="input" type="date" />
        </label>
        <button type="button" class="btn" :disabled="refreshing" @click="refreshAll">
          {{ refreshing ? 'Refreshing…' : 'Refresh Investments' }}
        </button>
        <span v-if="refreshMsg" class="msg" role="status">{{ refreshMsg }}</span>
      </div>
      <div class="link-box">
        <h3 class="text-md font-medium mb-1">Link New Investments Account</h3>
        <LinkProviderLauncher
          v-slot="{ linkPlaid, loading: linking, isDisabled, errorMessage, statusMessage }"
          :selected-products="['investments']"
          :user-id="plaidUserId"
          @refresh="onLinked"
        >
          <button
            type="button"
            class="btn"
            :disabled="isDisabled"
            data-testid="link-investments"
            @click="linkPlaid"
          >
            {{ linking ? 'Opening Plaid…' : 'Link investments account' }}
          </button>
          <p v-if="statusMessage" class="msg" role="status">{{ statusMessage }}</p>
          <p v-if="errorMessage" class="text-negative" role="alert">{{ errorMessage }}</p>
        </LinkProviderLauncher>
      </div>
    </section>
  </BasePageLayout>
</template>

<script setup>
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { ref, onMounted, computed, onBeforeUnmount, watch } from 'vue'
import {
  fetchHoldings,
  refreshInvestmentsAll,
  fetchInvestmentAccounts,
  fetchInvestmentTransactions,
} from '@/api/investments'
import PortfolioAllocationChart from '@/components/charts/PortfolioAllocationChart.vue'
import LinkProviderLauncher from '@/components/forms/LinkProviderLauncher.vue'
import { TrendingUp } from 'lucide-vue-next'

// Core state
const holdings = ref([])
const loading = ref(false)
const refreshing = ref(false)
const refreshMsg = ref('')
const today = new Date().toISOString().slice(0, 10)
const startDefault = new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString().slice(0, 10)
const startDate = ref(startDefault)
const endDate = ref(today)
const plaidUserId = import.meta.env.VITE_USER_ID_PLAID || import.meta.env.VITE_USER_ID || ''

const sectionNavItems = [
  { key: 'overview', label: 'Portfolio', target: 'portfolio-overview' },
  { key: 'holdings', label: 'Holdings', target: 'holdings' },
  { key: 'performance', label: 'Performance', target: 'performance' },
  { key: 'transactions', label: 'Activity', target: 'investment-transactions' },
  { key: 'maintenance', label: 'Manage', target: 'maintenance' },
]
const activeSection = ref(sectionNavItems[0].key)
const overviewSection = ref(null)
const holdingsSection = ref(null)
const performanceSection = ref(null)
const transactionsSection = ref(null)
const maintenanceSection = ref(null)
const sectionRefs = {
  overview: overviewSection,
  holdings: holdingsSection,
  performance: performanceSection,
  transactions: transactionsSection,
  maintenance: maintenanceSection,
}

function scrollToSection(key) {
  activeSection.value = key
  const section = sectionRefs[key]?.value
  if (section) {
    section.scrollIntoView({ behavior: 'smooth', block: 'start' })
    // Move keyboard focus to the section so the next Tab continues from its content.
    section.focus?.({ preventScroll: true })
  }
}

/** Clear every investment transaction filter and reload from page 1. */
function resetTxFilters() {
  txAccountId.value = ''
  txSecurityId.value = ''
  txType.value = ''
  txSubtype.value = ''
  txStartDate.value = ''
  txEndDate.value = ''
}

function handleScroll() {
  const anchor = 120
  let currentKey = sectionNavItems[0]?.key
  for (const item of sectionNavItems) {
    const section = sectionRefs[item.key]?.value
    if (!section) continue
    const rect = section.getBoundingClientRect()
    if (rect.top - anchor <= 0) {
      currentKey = item.key
    } else {
      break
    }
  }
  if (currentKey) {
    activeSection.value = currentKey
  }
}

// Accounts and filters
const accounts = ref([])
const selectedInstitution = ref('')
const selectedAccount = ref('')
const expandedHoldingAccounts = ref([])

// Derived
const uniqueSecurityCount = computed(() => new Set(holdings.value.map((h) => h.security_id)).size)
const institutions = computed(() =>
  Array.from(new Set(accounts.value.map((a) => a.institution_name).filter(Boolean))).sort(),
)
const accountsForInstitution = computed(() =>
  selectedInstitution.value
    ? accounts.value.filter((a) => a.institution_name === selectedInstitution.value)
    : accounts.value,
)
const accountLabelById = computed(() =>
  accounts.value.reduce((m, a) => {
    m[a.account_id] = accDisplay(a)
    return m
  }, {}),
)
function accDisplay(a) {
  return a.institution_name ? `${a.institution_name} • ${a.name}` : a.name
}
const filteredHoldings = computed(() => {
  const accId = selectedAccount.value
  if (accId) return holdings.value.filter((h) => h.account_id === accId)
  const inst = selectedInstitution.value
  if (inst) {
    const ids = new Set(
      accounts.value.filter((a) => a.institution_name === inst).map((a) => a.account_id),
    )
    return holdings.value.filter((h) => ids.has(h.account_id))
  }
  return holdings.value
})
const filteredAccountIds = computed(() =>
  Array.from(new Set(filteredHoldings.value.map((h) => h.account_id))),
)
const showAggregateHoldings = computed(
  () => !selectedAccount.value && filteredAccountIds.value.length > 1,
)
const summarizedHoldings = computed(() => {
  const byAccount = new Map()
  for (const holding of filteredHoldings.value) {
    if (!byAccount.has(holding.account_id)) {
      const account = accounts.value.find((entry) => entry.account_id === holding.account_id)
      byAccount.set(holding.account_id, {
        account_id: holding.account_id,
        institution_name: account?.institution_name || '',
        holdings_count: 0,
        securities_count: 0,
        total_value: 0,
        holdings: [],
      })
    }
    const summary = byAccount.get(holding.account_id)
    summary.holdings.push(holding)
    summary.holdings_count += 1
    summary.total_value += holdingValue(holding)
  }
  return Array.from(byAccount.values())
    .map((summary) => ({
      ...summary,
      securities_count: new Set(summary.holdings.map((holding) => holding.security_id)).size,
      holdings: [...summary.holdings].sort(
        (left, right) => holdingValue(right) - holdingValue(left),
      ),
    }))
    .sort((left, right) => right.total_value - left.total_value)
})

function toggleHoldingAccount(accountId) {
  if (expandedHoldingAccounts.value.includes(accountId)) {
    expandedHoldingAccounts.value = expandedHoldingAccounts.value.filter((id) => id !== accountId)
    return
  }
  expandedHoldingAccounts.value = [...expandedHoldingAccounts.value, accountId]
}

// Helpers
function formatNum(n) {
  const num = Number(n)
  if (Number.isNaN(num)) return '—'
  return num.toLocaleString(undefined, { maximumFractionDigits: 4 })
}
function formatCurrency(n) {
  const num = Number(n)
  if (Number.isNaN(num)) return '—'
  return num.toLocaleString(undefined, { style: 'currency', currency: 'USD' })
}
function holdingValue(h) {
  const v = Number(h.institution_value)
  if (!Number.isNaN(v) && v !== 0) return v
  const q = Number(h.quantity),
    p = Number(h?.security?.price)
  return Number.isNaN(q) || Number.isNaN(p) ? 0 : q * p
}

// Portfolio totals and allocation
const isFilteredHoldings = computed(() => filteredHoldings.value.length !== holdings.value.length)
const TX_ACTIVITY_LABELS = {
  buy: 'Buys',
  sell: 'Sells',
  dividend: 'Dividends',
  transfer: 'Transfers',
  cash: 'Cash',
  fee: 'Fees',
}
/**
 * Page-only activity grouped by provider type. Amounts of unlike activity are never
 * combined into a single profit or net figure.
 */
const txActivityGroups = computed(() => {
  const groups = new Map()
  for (const tx of txData.value) {
    const subtype = String(tx.subtype || '').toLowerCase()
    const type = String(tx.type || '').toLowerCase()
    const key = subtype.includes('dividend') ? 'dividend' : type || 'other'
    if (!groups.has(key)) {
      groups.set(key, { key, label: TX_ACTIVITY_LABELS[key] || 'Other', count: 0, amount: 0 })
    }
    const group = groups.get(key)
    group.count += 1
    group.amount += Number(tx.amount) || 0
  }
  return Array.from(groups.values())
})
const portfolioTotal = computed(() => holdings.value.reduce((s, h) => s + holdingValue(h), 0))
const filteredTotal = computed(() =>
  filteredHoldings.value.reduce((s, h) => s + holdingValue(h), 0),
)
const allocationByType = computed(() => {
  const map = new Map()
  for (const h of filteredHoldings.value) {
    const key = h.security?.type || 'Unknown'
    map.set(key, (map.get(key) || 0) + holdingValue(h))
  }
  return Array.from(map.entries()).map(([label, value]) => ({ label, value }))
})
const totalsByInstitution = computed(() => {
  const out = {}
  for (const h of filteredHoldings.value) {
    const inst =
      accounts.value.find((a) => a.account_id === h.account_id)?.institution_name || 'Unknown'
    out[inst] = (out[inst] || 0) + holdingValue(h)
  }
  return out
})

// Loaders
async function load() {
  loading.value = true
  try {
    const res = await fetchHoldings(plaidUserId)
    holdings.value = res?.data || []
  } finally {
    loading.value = false
  }
}

async function loadAccounts() {
  try {
    const res = await fetchInvestmentAccounts(plaidUserId)
    const data = res?.data || res?.data?.accounts || res?.accounts || []
    accounts.value = (Array.isArray(data) ? data : []).map((a) => ({
      account_id: a.account_id,
      name: a.name,
      institution_name: a.institution_name,
    }))
  } catch (_error) {
    // Ignore and keep existing account list when request fails.
  }
}

// Transactions (paginated)
const txPage = ref(1)
const txPageSize = 10
const txTotal = ref(0)
const txData = ref([])
const txLoading = ref(false)
const txAccountId = ref('')
const txSecurityId = ref('')
const txType = ref('')
const txSubtype = ref('')
const txStartDate = ref('')
const txEndDate = ref('')
const TX_FILTER_STORAGE_KEY = 'investments.transactionFilters'
const txFilterRestoreInProgress = ref(false)
const activeTxFilterCount = computed(
  () =>
    [txAccountId, txSecurityId, txType, txSubtype, txStartDate, txEndDate].filter((f) => f.value)
      .length,
)
const txTotalPages = computed(() => Math.max(1, Math.ceil(txTotal.value / txPageSize)))

/**
 * Build the transactions filter payload using backend query parameter names.
 *
 * @returns {Record<string, string>} API-ready filter params.
 */
function buildTransactionFilters() {
  const filters = {}
  if (txAccountId.value) filters.account_id = txAccountId.value
  if (txSecurityId.value) filters.security_id = txSecurityId.value
  if (txType.value) filters.type = txType.value
  if (txSubtype.value) filters.subtype = txSubtype.value
  if (txStartDate.value) filters.start_date = txStartDate.value
  if (txEndDate.value) filters.end_date = txEndDate.value
  return filters
}

/**
 * Persist investment transaction filters to local storage.
 */
function persistTransactionFilters() {
  try {
    localStorage.setItem(TX_FILTER_STORAGE_KEY, JSON.stringify(buildTransactionFilters()))
  } catch (_error) {
    // Ignore storage write failures (e.g., private mode restrictions).
  }
}

/**
 * Restore persisted transaction filters from local storage.
 */
function restoreTransactionFilters() {
  txFilterRestoreInProgress.value = true
  try {
    const raw = localStorage.getItem(TX_FILTER_STORAGE_KEY)
    const stored = raw ? JSON.parse(raw) : {}
    txAccountId.value = stored.account_id || ''
    txSecurityId.value = stored.security_id || ''
    txType.value = stored.type || ''
    txSubtype.value = stored.subtype || ''
    txStartDate.value = stored.start_date || ''
    txEndDate.value = stored.end_date || ''
  } catch (_error) {
    // Ignore malformed local storage payloads and reset filters.
    txAccountId.value = ''
    txSecurityId.value = ''
    txType.value = ''
    txSubtype.value = ''
    txStartDate.value = ''
    txEndDate.value = ''
  } finally {
    txFilterRestoreInProgress.value = false
  }
}

async function loadTransactions(page = 1) {
  txLoading.value = true
  try {
    txPage.value = page
    const filters = { user_id: plaidUserId, ...buildTransactionFilters() }
    const res = await fetchInvestmentTransactions(page, txPageSize, filters)
    const payload = res?.data || res || {}
    txData.value = payload.transactions || payload.data?.transactions || []
    txTotal.value = payload.total || payload.data?.total || 0
  } finally {
    txLoading.value = false
  }
}

watch([txAccountId, txSecurityId, txType, txSubtype, txStartDate, txEndDate], async () => {
  if (txFilterRestoreInProgress.value) return
  persistTransactionFilters()
  await loadTransactions(1)
})

watch(selectedInstitution, (institution) => {
  if (!institution) return
  const validAccountIds = new Set(
    accounts.value
      .filter((account) => account.institution_name === institution)
      .map((account) => account.account_id),
  )
  if (selectedAccount.value && !validAccountIds.has(selectedAccount.value)) {
    selectedAccount.value = ''
  }
})

watch([filteredAccountIds, showAggregateHoldings], ([accountIds, aggregate]) => {
  if (!aggregate) {
    expandedHoldingAccounts.value = []
    return
  }
  const allowedIds = new Set(accountIds)
  expandedHoldingAccounts.value = expandedHoldingAccounts.value.filter((id) => allowedIds.has(id))
})

onMounted(async () => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  restoreTransactionFilters()
  await Promise.all([load(), loadAccounts()])
  await loadTransactions(1)
  handleScroll()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
})

// Refresh
async function refreshAll() {
  refreshing.value = true
  refreshMsg.value = ''
  try {
    const res = await refreshInvestmentsAll({
      start_date: startDate.value,
      end_date: endDate.value,
    })
    const s = res?.summary || {}
    refreshMsg.value = `Upserted ${s.holdings || 0} holdings, ${s.securities || 0} securities, ${s.investment_transactions || 0} transactions`
    await load()
    await loadTransactions(1)
  } catch (e) {
    refreshMsg.value = 'Refresh failed'
  } finally {
    refreshing.value = false
  }
}

function onLinked() {
  // After successful link, reload data
  load()
  loadAccounts()
  loadTransactions(1)
}
</script>

<style scoped>
@reference "../assets/css/main.css";

.investments-view {
  background-color: var(--page-bg);
  color: var(--theme-fg);
  min-height: 100vh;
}
.section-subnav {
  display: flex;
  flex-wrap: nowrap;
  gap: 0.25rem;
  overflow-x: auto;
  border-bottom: 1px solid var(--divider);
}
section[id] {
  scroll-margin-top: 5rem;
}
section[id]:focus {
  outline: none;
}
section[id]:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 4px;
}
.section-subnav__link {
  flex: 0 0 auto;
  white-space: nowrap;
  min-height: var(--control-height-sm);
  padding: 0.5rem 0.75rem;
  font-size: 0.9375rem;
  color: var(--color-text-muted);
  border-bottom: 2px solid transparent;
}
.section-subnav__link.is-active {
  color: var(--color-text-light);
  font-weight: 600;
  border-bottom-color: var(--accent-primary);
}
.section-subnav__link:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 2px;
}
.filters-disclosure > summary {
  cursor: pointer;
  min-height: var(--control-height-sm);
  font-size: 0.9375rem;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}
.metric--lead .v {
  font-size: 1.75rem;
}
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
}
@media (max-width: 1023px) {
  .overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 479px) {
  .overview-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
.metric {
  background: var(--themed-bg);
  border: 1px solid var(--divider);
  border-radius: 8px;
  padding: 0.75rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 0.75rem;
  justify-content: space-between;
  min-width: 0;
}
.metric .k {
  color: var(--text-muted);
}
.metric .v {
  font-weight: 700;
  overflow-wrap: anywhere;
  min-width: 0;
}
.controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}
.controls label {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  align-items: center;
  max-width: 100%;
  min-width: 0;
}
.controls input[type='date'] {
  width: auto;
  min-width: 0;
  max-width: 100%;
  flex: 1 1 min(100%, 10rem);
}
.controls .btn {
  padding: 0.4rem 0.7rem;
  border: 1px solid var(--divider);
  border-radius: 6px;
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: var(--accent-primary-contrast);
  cursor: pointer;
}
.controls .msg {
  color: var(--text-muted);
}
.totals-bar {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--divider);
}
.totals-bar .muted {
  color: var(--text-muted);
}
.filters {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin: 0.5rem 0 0.75rem;
  flex-wrap: wrap;
}
.filters label {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  align-items: center;
  max-width: 100%;
  min-width: 0;
}
.filters select,
.filters input {
  width: auto;
  min-width: 0;
  max-width: 100%;
  flex: 1 1 min(100%, 10rem);
}
.filters--grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 12rem), 1fr));
  align-items: end;
}
.filters--grid label {
  display: flex;
  flex-direction: column;
  align-items: stretch;
}
.filters--grid select,
.filters--grid input {
  width: 100%;
}
/* Tables scroll inside their own region instead of overflowing the page. */
.holdings-table,
.tx-table {
  border: 1px solid var(--divider);
  border-radius: 8px;
  overflow-x: auto;
  overscroll-behavior-x: contain;
}
.holdings-table:focus-visible,
.tx-table:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: -2px;
}
.thead,
.trow,
.holdings-details-head,
.holdings-details-row {
  min-width: 40rem;
}
.thead,
.trow {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr 2fr 0.8fr 0.8fr 0.9fr;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
}
.thead {
  background: var(--themed-bg);
  font-weight: 600;
}
.trow {
  border-top: 1px solid var(--divider);
}
.holdings-summary-row {
  width: 100%;
  border: 0;
  border-top: 1px solid var(--divider);
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: left;
}
.holdings-summary-row:hover {
  background: color-mix(in srgb, var(--color-accent-cyan) 8%, transparent);
}
.holdings-summary-row:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: -2px;
}
.trow .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.expand-cell {
  text-align: right;
  font-weight: 600;
}
.holdings-summary-head,
.holdings-summary-row {
  grid-template-columns: 1.8fr 1.2fr 0.8fr 0.8fr 1fr 0.7fr;
}
.holdings-details-panel {
  border-top: 1px solid var(--divider);
  background: color-mix(in srgb, var(--themed-bg) 88%, black 12%);
  padding: 0.25rem 0.75rem 0.75rem;
}
.holdings-details-head,
.holdings-details-row {
  display: grid;
  grid-template-columns: 0.8fr 2fr 0.8fr 0.8fr 0.9fr;
  gap: 0.5rem;
  padding: 0.45rem 0.25rem;
}
.holdings-details-head {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
}
.holdings-details-row + .holdings-details-row {
  border-top: 1px solid color-mix(in srgb, var(--divider) 75%, transparent);
}
.holdings-note {
  margin-top: 0.5rem;
}
/* Long security names wrap so the full text stays readable (also in the title tooltip). */
.name-clip {
  overflow-wrap: anywhere;
  min-width: 0;
}
.inst-summary {
  margin-top: 0.5rem;
  border: 1px dashed var(--divider);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
}
.inst-row {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
}
.perf-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
}
.tx-activity {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.tx-activity__groups {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
  font-variant-numeric: tabular-nums;
}

.pager {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  align-items: center;
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--divider);
}
.pager .btn {
  padding: 0.25rem 0.6rem;
  border: 1px solid var(--divider);
  border-radius: 6px;
  background: var(--themed-bg);
  color: inherit;
  cursor: pointer;
}
</style>
