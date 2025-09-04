<!-- Investments.vue - Skeleton layout for the future Investments dashboard. -->
<template>
  <BasePageLayout class="investments-view" gap="gap-8">
    <h1 class="text-2xl font-bold">Investments</h1>

    <section>
      <h2 class="text-xl font-semibold mb-2">Portfolio Overview</h2>
      <div class="link-box">
        <h3 class="text-md font-medium mb-1">Link New Investments Account</h3>
        <LinkProviderLauncher :selected-products="['investments']" :user-id="plaidUserId" @refresh="onLinked" />
      </div>
      <div class="controls">
        <label>
          <span>Start</span>
          <input type="date" v-model="startDate" />
        </label>
        <label>
          <span>End</span>
          <input type="date" v-model="endDate" />
        </label>
        <button class="btn" :disabled="refreshing" @click="refreshAll">
          {{ refreshing ? 'Refreshing…' : 'Refresh Investments' }}
        </button>
        <span v-if="refreshMsg" class="msg">{{ refreshMsg }}</span>
      </div>
      <div class="text-muted" v-if="loading">Loading…</div>
      <div v-else class="overview-grid">
        <div class="metric">
          <span class="k">Holdings</span><span class="v">{{ holdings.length }}</span>
        </div>
        <div class="metric">
          <span class="k">Securities</span><span class="v">{{ uniqueSecurityCount }}</span>
        </div>
      </div>
    </section>

    <section>
      <h2 class="text-xl font-semibold mb-2">Holdings</h2>
      <div class="filters">
        <label>
          <span>Institution</span>
          <select v-model="selectedInstitution">
            <option value="">All</option>
            <option v-for="inst in institutions" :key="inst" :value="inst">{{ inst }}</option>
          </select>
        </label>
        <label>
          <span>Account</span>
          <select v-model="selectedAccount">
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
      <div v-else class="holdings-table">
        <div class="totals-bar">
          <div>
            Total (filtered): <strong>{{ formatCurrency(filteredTotal) }}</strong>
          </div>
          <div class="muted">Portfolio total: {{ formatCurrency(portfolioTotal) }}</div>
        </div>
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
          <div class="name-clip">{{ h.security?.name || h.security_id }}</div>
          <div class="num">{{ formatNum(h.quantity) }}</div>
          <div class="num">{{ formatCurrency(h.security?.price) }}</div>
          <div class="num">{{ formatCurrency(holdingValue(h)) }}</div>
        </div>
      </div>
      <div v-if="Object.keys(totalsByInstitution).length" class="inst-summary">
        <div class="inst-row" v-for="(val, inst) in totalsByInstitution" :key="inst">
          <span class="inst">{{ inst }}</span>
          <span class="val">{{ formatCurrency(val) }}</span>
        </div>
      </div>
    </section>

    <section>
      <h2 class="text-xl font-semibold mb-2">Performance</h2>
      <div class="perf-grid">
        <PortfolioAllocationChart :allocations="allocationByType" />
      </div>
    </section>

    <section>
      <h2 class="text-xl font-semibold mb-2">Recent Investment Transactions</h2>
      <div class="filters">
        <label>
          <span>Account</span>
          <select v-model="txAccountId" @change="loadTransactions(1)">
            <option value="">All</option>
            <option v-for="acc in accounts" :key="acc.account_id" :value="acc.account_id">
              {{ accDisplay(acc) }}
            </option>
          </select>
        </label>
      </div>
      <div v-if="txLoading" class="text-muted">Loading transactions…</div>
      <div v-else>
        <div v-if="txData.length === 0" class="text-muted">No transactions found.</div>
        <div v-else class="tx-table">
          <div class="thead">
            <div>Date</div>
            <div>Account</div>
            <div>Security</div>
            <div>Name</div>
            <div class="num">Qty</div>
            <div class="num">Price</div>
            <div class="num">Amount</div>
          </div>
          <div v-for="tx in txData" :key="tx.investment_transaction_id" class="trow">
            <div>{{ (tx.date || '').slice(0, 10) }}</div>
            <div>{{ accountLabelById[tx.account_id] || tx.account_id }}</div>
            <div>{{ tx.security_id || '—' }}</div>
            <div class="name-clip">{{ tx.name || tx.subtype || tx.type }}</div>
            <div class="num">{{ formatNum(tx.quantity) }}</div>
            <div class="num">{{ formatCurrency(tx.price) }}</div>
            <div class="num">{{ formatCurrency(tx.amount) }}</div>
          </div>
          <div class="pager">
            <button class="btn" :disabled="txPage === 1" @click="loadTransactions(txPage - 1)">
              Prev
            </button>
            <span>Page {{ txPage }} of {{ txTotalPages }}</span>
            <button
              class="btn"
              :disabled="txPage === txTotalPages"
              @click="loadTransactions(txPage + 1)"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </section>
  </BasePageLayout>
</template>

<script setup>
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import { ref, onMounted, computed } from 'vue'
import {
  fetchHoldings,
  refreshInvestmentsAll,
  fetchInvestmentAccounts,
  fetchInvestmentTransactions,
} from '@/api/investments'
import PortfolioAllocationChart from '@/components/charts/PortfolioAllocationChart.vue'
import LinkProviderLauncher from '@/components/forms/LinkProviderLauncher.vue'

// Core state
const holdings = ref([])
const loading = ref(false)
const refreshing = ref(false)
const refreshMsg = ref('')
const today = new Date().toISOString().slice(0, 10)
const startDefault = new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString().slice(0, 10)
const startDate = ref(startDefault)
const endDate = ref(today)
const plaidUserId = import.meta.env.VITE_USER_ID_PLAID || ''

// Accounts and filters
const accounts = ref([])
const selectedInstitution = ref('')
const selectedAccount = ref('')

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
    const res = await fetchHoldings()
    holdings.value = res?.data || []
  } finally {
    loading.value = false
  }
}

async function loadAccounts() {
  try {
    const res = await fetchInvestmentAccounts()
    const data = res?.data || res?.data?.accounts || res?.accounts || []
    accounts.value = (Array.isArray(data) ? data : []).map((a) => ({
      account_id: a.account_id,
      name: a.name,
      institution_name: a.institution_name,
    }))
  } catch {}
}

// Transactions (paginated)
const txPage = ref(1)
const txPageSize = 10
const txTotal = ref(0)
const txData = ref([])
const txLoading = ref(false)
const txAccountId = ref('')
const txTotalPages = computed(() => Math.max(1, Math.ceil(txTotal.value / txPageSize)))

async function loadTransactions(page = 1) {
  txLoading.value = true
  try {
    txPage.value = page
    const filters = {}
    if (txAccountId.value) filters.account_id = txAccountId.value
    const res = await fetchInvestmentTransactions(page, txPageSize, filters)
    const payload = res?.data || res || {}
    txData.value = payload.transactions || payload.data?.transactions || []
    txTotal.value = payload.total || payload.data?.total || 0
  } finally {
    txLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([load(), loadAccounts()])
  await loadTransactions(1)
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
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
}
.metric {
  background: var(--themed-bg);
  border: 1px solid var(--divider);
  border-radius: 8px;
  padding: 0.75rem;
  display: flex;
  justify-content: space-between;
}
.metric .k {
  color: #6b7280;
}
.metric .v {
  font-weight: 700;
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
  gap: 0.25rem;
  align-items: center;
}
.controls input[type='date'] {
  padding: 0.25rem 0.4rem;
  border: 1px solid var(--divider);
  background: var(--themed-bg);
  color: inherit;
  border-radius: 6px;
}
.controls .btn {
  padding: 0.4rem 0.7rem;
  border: 1px solid var(--divider);
  border-radius: 6px;
  background: var(--color-accent-cyan, #06b6d4);
  color: #fff;
  cursor: pointer;
}
.controls .msg {
  color: #6b7280;
}
.totals-bar {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--divider);
}
.totals-bar .muted {
  color: #6b7280;
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
  gap: 0.25rem;
  align-items: center;
}
.filters select {
  padding: 0.25rem 0.4rem;
  border: 1px solid var(--divider);
  background: var(--themed-bg);
  color: inherit;
  border-radius: 6px;
}
.holdings-table {
  border: 1px solid var(--divider);
  border-radius: 8px;
  overflow: hidden;
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
.trow .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.name-clip {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
.tx-table {
  border: 1px solid var(--divider);
  border-radius: 8px;
  overflow: hidden;
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
