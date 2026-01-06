<template>
  <div class="card table-panel">
    <h3 class="table-title font-bold text-xl mb-6 text-left tracking-wide flex items-center">
      <span class="title-icon i-ph:currency-circle-dollar-duotone text-2xl mr-2"></span>
      Recent Transactions
    </h3>
    <div class="control-surface md:flex-row md:items-center">
      <DateRangeSelector
        :start-date="startDate"
        :end-date="endDate"
        disable-zoom
        @update:startDate="startDate = $event"
        @update:endDate="endDate = $event"
      />
      <div class="control-group">
        <label class="control-label" for="account-filter">Account</label>
        <select
          id="account-filter"
          v-model="accountId"
          data-test="account-filter"
          class="control-select"
        >
          <option value="">All Accounts</option>
          <option v-for="acc in accounts" :key="acc.account_id" :value="acc.account_id">
            {{ formatName(acc.name) }}
          </option>
        </select>
      </div>
      <div class="control-group">
        <label class="control-label" for="type-filter">Type</label>
        <div class="pill-row">
          <button
            class="pill md:text-sm"
            :class="{ active: txType === '' }"
            @click="txType = ''"
            type="button"
          >
            All
          </button>
          <button
            class="pill md:text-sm"
            :class="{ active: txType === 'credit' }"
            @click="txType = 'credit'"
            type="button"
          >
            Credit
          </button>
          <button
            class="pill md:text-sm"
            :class="{ active: txType === 'debit' }"
            @click="txType = 'debit'"
            type="button"
          >
            Debit
          </button>
        </div>
      </div>
    </div>
    <div v-if="activeFilters.length" class="filter-tags" data-testid="transactions-filter-tags">
      <span v-for="filter in activeFilters" :key="filter.key" class="filter-tag">
        <span class="filter-tag__label">{{ filter.label }}:</span>
        <span class="filter-tag__value">{{ filter.value }}</span>
        <button type="button" class="filter-tag__remove" @click="removeFilter(filter.key)">
          ×
        </button>
      </span>
    </div>
    <div class="mb-8">
      <canvas ref="transactionsChart" height="110"></canvas>
    </div>
    <div class="table-shell">
      <table class="data-table">
        <thead class="table-head">
          <tr>
            <th class="th-cell text-left">Date</th>
            <th class="th-cell text-left">Category</th>
            <th class="th-cell text-left">Merchant: Description</th>
            <th class="th-cell text-left">Institution / Account</th>
            <th class="th-cell text-right">Amount</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tx in transactions" :key="tx.transaction_id" class="table-row">
            <!-- Date -->
            <td class="cell font-mono text-xs cell-muted">{{ formatDate(tx.date) }}</td>
            <!-- Category -->
            <td class="cell text-center">
              <img
                v-if="tx.category_icon_url"
                :src="tx.category_icon_url"
                alt="category icon"
                class="h-5 w-5 mx-auto"
                loading="lazy"
              />
              <span
                v-else
                :class="[
                  'inline-block rounded-xl border border-[var(--divider)] bg-[var(--color-bg-secondary)]',
                  'px-3 py-1 text-xs font-semibold text-[color:var(--color-accent-blue)] tracking-wide shadow-sm',
                ]"
              >
                {{ formatCategory(tx) }}
              </span>
            </td>
            <!-- Merchant: Description -->
            <td class="cell font-medium truncate max-w-xs">
              {{ formatDescription(tx) }}
            </td>
            <!-- Institution: Account with icon -->
            <td class="cell text-xs cell-flex text-[color:var(--text-primary)]">
              <img
                v-if="tx.institution_icon_url"
                :src="tx.institution_icon_url"
                alt=""
                class="h-5 w-5 rounded-full border border-[var(--divider)] bg-[var(--color-bg)] object-contain"
                loading="lazy"
              />
              <span class="font-medium">{{ formatName(tx.institution_name) }}</span>
              <span
                v-if="tx.institution_name && tx.account_name"
                class="mx-1 text-[color:var(--color-text-muted)]"
                >/</span
              >
              <span>{{ formatName(tx.account_name) }}</span>
            </td>
            <!-- Amount -->
            <td
              class="cell font-mono text-right text-base font-semibold"
              :class="{
                'text-[color:var(--color-accent-cyan)]': tx.amount > 0,
                'text-[color:var(--color-accent-red)]': tx.amount < 0,
                'text-[color:var(--color-text-muted)]': tx.amount === 0 || !tx.amount,
              }"
            >
              {{ formatAmount(tx.amount) }}
            </td>
          </tr>
          <tr v-if="transactions.length === 0">
            <td
              :colspan="5"
              class="cell py-8 text-center text-[color:var(--color-text-muted)] italic"
            >
              No transactions found.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <PaginationControls
      v-if="totalPages > 1"
      :current-page="page"
      :total-pages="totalPages"
      :page-size="pageSize"
      :total-items="total"
      @change-page="setPage"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import Chart from 'chart.js/auto'
import DateRangeSelector from '../DateRangeSelector.vue'
import PaginationControls from './PaginationControls.vue'
import { fetchTransactions } from '@/api/transactions'
import { formatAmount as formatCurrency } from '@/utils/format'

/**
 * TransactionsTable
 *
 * Displays a paginated table of transactions with date range,
 * account and type filters. Active filters are displayed as tags and can
 * be cleared individually. Data is fetched from the backend `/transactions`
 * endpoint using the provided filters.
 */
export default {
  name: 'TransactionsTable',
  components: { DateRangeSelector, PaginationControls },
  setup() {
    const transactionsChart = ref(null)
    const transactions = ref([])
    const accounts = ref([])
    const page = ref(1)
    const pageSize = 15
    const total = ref(0)
    const accountId = ref('')
    const txType = ref('')
    const today = new Date()
    const defaultEndDate = today.toISOString().slice(0, 10)
    const defaultStartDate = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .slice(0, 10)
    const endDate = ref(defaultEndDate)
    const startDate = ref(defaultStartDate)

    const totalPages = computed(() => Math.ceil(total.value / pageSize))
    const accountLookup = computed(
      () => new Map(accounts.value.map((account) => [account.account_id, account.name])),
    )

    async function load() {
      const params = {
        page: page.value,
        page_size: pageSize,
      }
      if (startDate.value) params.start_date = startDate.value
      if (endDate.value) params.end_date = endDate.value
      if (accountId.value) params.account_ids = accountId.value
      if (txType.value) params.tx_type = txType.value
      const res = await fetchTransactions(params)
      transactions.value = (res.transactions || []).slice().sort((a, b) => {
        const aTime = new Date(a?.date || 0).getTime()
        const bTime = new Date(b?.date || 0).getTime()
        return bTime - aTime
      })
      total.value = res.total || 0
      updateChart()
    }

    async function fetchAccounts() {
      const resp = await fetch('/api/accounts/get_accounts')
      const data = await resp.json()
      if (data.status === 'success') {
        accounts.value = data.accounts
      }
    }

    function updateChart() {
      if (!transactionsChart.value) return
      const map = {}
      transactions.value.forEach((tx) => {
        if (!tx.date) return
        const d = new Date(tx.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        map[d] = (map[d] || 0) + Number(tx.amount || 0)
      })
      const keys = Object.keys(map).slice(-7)
      new Chart(transactionsChart.value.getContext('2d'), {
        type: 'line',
        data: {
          labels: keys,
          datasets: [
            {
              label: 'Daily Net',
              data: keys.map((k) => map[k]),
              fill: false,
              tension: 0.3,
              borderColor: '#61e8fc',
              backgroundColor: '#61e8fc55',
              pointBorderColor: '#39ff14',
              pointBackgroundColor: '#232e46',
              pointRadius: 5,
              pointHoverRadius: 8,
              borderWidth: 2.5,
            },
          ],
        },
        options: {
          plugins: {
            legend: {
              labels: {
                color: '#61e8fc',
                font: { family: 'Fira Mono, monospace', size: 13, weight: 'bold' },
              },
            },
            tooltip: {
              backgroundColor: '#232e46',
              titleColor: '#61e8fc',
              bodyColor: '#e4f5fd',
              borderColor: '#61e8fc',
              borderWidth: 1,
              caretSize: 8,
              displayColors: false,
            },
          },
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              grid: { color: 'rgba(97,232,252,0.12)' },
              ticks: { color: '#9bb2cf', font: { family: 'Fira Mono, monospace', size: 12 } },
            },
            y: {
              grid: { color: 'rgba(97,232,252,0.10)' },
              ticks: { color: '#9bb2cf', font: { family: 'Fira Mono, monospace', size: 12 } },
            },
          },
        },
      })
    }

    function setPage(target) {
      const clamped = Math.max(1, Math.min(target, totalPages.value || 1))
      if (clamped !== page.value) {
        page.value = clamped
      }
      load()
    }

    function nextPage() {
      if (page.value < totalPages.value) {
        setPage(page.value + 1)
      }
    }
    function prevPage() {
      if (page.value > 1) {
        setPage(page.value - 1)
      }
    }

    /**
     * Provide a user-friendly label for an account id.
     * @param {string} id - Account identifier.
     * @returns {string} Display label for the account filter.
     */
    function formatAccountLabel(id) {
      return formatName(accountLookup.value.get(id) || id)
    }

    /**
     * Reset a single filter tag by key.
     * @param {string} key - Filter tag key.
     */
    function removeFilter(key) {
      if (key === 'account') {
        accountId.value = ''
        return
      }
      if (key === 'type') {
        txType.value = ''
        return
      }
      if (key === 'date') {
        startDate.value = ''
        endDate.value = ''
      }
    }

    const activeFilters = computed(() => {
      const filters = []
      if (startDate.value || endDate.value) {
        const startLabel = startDate.value || 'Any'
        const endLabel = endDate.value || 'Any'
        filters.push({ key: 'date', label: 'Dates', value: `${startLabel} → ${endLabel}` })
      }
      if (accountId.value) {
        filters.push({
          key: 'account',
          label: 'Account',
          value: formatAccountLabel(accountId.value),
        })
      }
      if (txType.value) {
        filters.push({
          key: 'type',
          label: 'Type',
          value: txType.value === 'credit' ? 'Credit' : 'Debit',
        })
      }
      return filters
    })

    // Formatting methods
    const formatDate = (dateStr) => {
      if (!dateStr) return 'N/A'
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', {
        year: '2-digit',
        month: 'short',
        day: 'numeric',
      })
    }
    const formatAmount = (amount) => formatCurrency(amount)
    const formatDescription = (tx) => {
      const merchant = tx.merchant_name ? toTitleCase(tx.merchant_name) : ''
      const desc = tx.description ? literaryFormat(tx.description) : ''
      if (merchant && desc) return `${merchant}: ${desc}`
      if (merchant) return merchant
      if (desc) return desc
      return ''
    }
    const formatCategory = (tx) => {
      const p = tx.primary_category || ''
      const d = tx.detailed_category || ''
      if (p && d) return `${capitalizeFirst(p)}: ${capitalizeFirst(d)}`
      if (p) return capitalizeFirst(p)
      if (d) return capitalizeFirst(d)
      return 'Unknown'
    }
    const capitalizeFirst = (str) =>
      !str ? '' : str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
    const literaryFormat = (str) =>
      !str ? '' : str.replace(/(^\s*\w|[.!?]\s*\w)/g, (s) => s.toUpperCase())
    // eslint-disable-next-line no-useless-escape
    const toTitleCase = (str) =>
      !str
        ? ''
        : str
            .toLowerCase()
            .replace(/([^\s\/-]+)(?=[\s\/-]?)/g, (w) => w.charAt(0).toUpperCase() + w.slice(1))
    const formatName = (val) =>
      !val
        ? 'N/A'
        : String(val)
            .toLowerCase()
            .replace(/(^|[\s/-])([a-z])/g, (_, sep, ch) => `${sep}${ch.toUpperCase()}`)

    watch([startDate, endDate, accountId, txType], () => {
      page.value = 1
      load()
    })

    onMounted(() => {
      fetchAccounts()
      load()
    })

    return {
      transactionsChart,
      transactions,
      accounts,
      accountId,
      txType,
      startDate,
      endDate,
      page,
      total,
      totalPages,
      activeFilters,
      formatDate,
      formatAmount,
      formatDescription,
      formatCategory,
      formatName,
      removeFilter,
      setPage,
      nextPage,
      prevPage,
    }
  },
}
</script>

<style scoped>
@reference "tailwindcss"; /* Keep Tailwind utilities available for scoped @apply (Tailwind v4) */

.table-panel {
  @apply shadow-xl rounded-2xl p-4 md:p-6;
  background-color: var(--table-surface-strong);
  border: 1px solid var(--table-border);
}

.table-title {
  color: var(--color-accent-blue);
}

.title-icon {
  color: var(--color-accent-blue);
}

.table-shell {
  @apply overflow-x-auto rounded-xl border;
  background-color: var(--table-surface);
  border-color: var(--table-border);
}

.data-table {
  @apply min-w-full text-sm;
  border-collapse: separate;
  border-spacing: 0;
}

.table-head {
  background-color: var(--table-header);
  border-bottom: 1px solid var(--table-border);
}

.th-cell {
  @apply py-3 px-4 text-left font-bold uppercase tracking-wider;
  color: var(--color-text-muted);
  border-right: 1px solid var(--table-border);
}

.th-cell:last-child {
  border-right: none;
}

.table-row {
  background-color: var(--table-surface);
  border-bottom: 1px solid var(--table-border);
  transition: background-color 150ms ease;
}

.table-row:nth-child(even) {
  background-color: var(--table-surface-alt);
}

.table-row:hover {
  background-color: var(--table-hover);
}

.cell {
  @apply px-4 py-2;
  color: var(--text-primary);
}

.cell-muted {
  color: var(--color-text-muted);
}

.cell-flex {
  @apply flex items-center gap-2;
}

.control-surface {
  @apply flex flex-col md:flex-row md:items-center gap-4 mb-4 rounded-2xl p-4 shadow-inner;
  background-color: var(--table-control);
  border: 1px solid var(--table-border);
}

.control-group {
  @apply flex flex-col gap-2 min-w-[160px];
}

.control-label {
  @apply text-xs uppercase tracking-wide;
  color: var(--color-text-muted);
}

.control-select {
  @apply rounded-xl px-3 py-2 shadow-sm outline-none transition;
  background-color: var(--table-surface);
  border: 1px solid var(--table-border);
  color: var(--text-primary);
}

.pill-row {
  @apply inline-flex gap-2;
}

.pill {
  @apply text-xs md:text-sm px-3 py-2 rounded-full border transition shadow-sm;
  background-color: var(--table-surface);
  border-color: var(--table-border);
  color: var(--text-primary);
}

.pill.active {
  background-color: var(--table-control);
  border-color: var(--color-accent-blue);
  color: var(--color-accent-blue);
}

.filter-tags {
  @apply flex flex-wrap items-center gap-2 mb-6;
}

.filter-tag {
  @apply inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs;
  background-color: color-mix(in srgb, var(--color-accent-blue) 12%, transparent);
  border: 1px solid var(--table-border);
  color: var(--text-primary);
}

.filter-tag__label {
  @apply uppercase tracking-wide text-[11px];
  color: var(--color-accent-blue);
}

.filter-tag__value {
  @apply font-semibold;
}

.filter-tag__remove {
  @apply transition;
  color: var(--color-accent-blue);
}
</style>
