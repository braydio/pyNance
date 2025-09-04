<template>
  <div class="card bg-neutral-950 border border-neutral-800 shadow-xl rounded-2xl p-4 md:p-6">
    <h3 class="font-bold text-xl mb-6 text-left tracking-wide text-blue-300 flex items-center">
      <span class="i-ph:currency-circle-dollar-duotone text-2xl mr-2 text-blue-400"></span>
      Recent Transactions
    </h3>
    <div class="flex flex-wrap items-center gap-4 mb-4">
      <DateRangeSelector
        :start-date="startDate"
        :end-date="endDate"
        disable-zoom
        @update:startDate="startDate = $event"
        @update:endDate="endDate = $event"
      />
      <select
        v-model="accountId"
        data-test="account-filter"
        class="select px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)]"
      >
        <option value="">All Accounts</option>
        <option v-for="acc in accounts" :key="acc.account_id" :value="acc.account_id">
          {{ acc.name }}
        </option>
      </select>
      <select
        v-model="txType"
        data-test="type-filter"
        class="select px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)]"
      >
        <option value="">All Types</option>
        <option value="credit">Credit</option>
        <option value="debit">Debit</option>
      </select>
    </div>
    <div class="mb-8">
      <canvas ref="transactionsChart" height="110"></canvas>
    </div>
    <div class="overflow-x-auto rounded-xl border border-neutral-800">
      <table class="min-w-full divide-y divide-neutral-800 text-sm">
        <thead class="bg-neutral-900 border-b border-blue-800">
          <tr>
            <th
              class="py-3 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800"
            >
              Date
            </th>
            <th
              class="py-3 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800"
            >
              Category
            </th>
            <th
              class="py-3 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800"
            >
              Merchant: Description
            </th>
            <th
              class="py-3 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800"
            >
              Institution / Account
            </th>
            <th class="py-3 px-4 text-right font-bold uppercase tracking-wider text-blue-200">
              Amount
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(tx, i) in transactions"
            :key="tx.transaction_id"
            :class="[
              i % 2 === 0 ? 'bg-neutral-950' : 'bg-neutral-900',
              'hover:bg-blue-950/60 transition-colors duration-100 border-b border-neutral-800',
            ]"
          >
            <!-- Date -->
            <td class="px-4 py-2 font-mono text-xs text-neutral-400">{{ formatDate(tx.date) }}</td>
            <!-- Category -->
            <td class="px-4 py-2 text-center">
              <img
                v-if="tx.category_icon_url"
                :src="tx.category_icon_url"
                alt="category icon"
                class="h-5 w-5 mx-auto"
                loading="lazy"
              />
              <span
                v-else
                class="inline-block rounded-xl border border-blue-800 bg-gradient-to-r from-neutral-900 to-blue-950 px-3 py-1 text-xs font-semibold text-blue-200 tracking-wide shadow-sm"
              >
                {{ formatCategory(tx) }}
              </span>
            </td>
            <!-- Merchant: Description -->
            <td class="px-4 py-2 font-medium text-neutral-100 truncate max-w-xs">
              {{ formatDescription(tx) }}
            </td>
            <!-- Institution: Account with icon -->
            <td class="px-4 py-2 text-xs text-neutral-300 flex items-center gap-2">
              <img
                v-if="tx.institution_icon_url"
                :src="tx.institution_icon_url"
                alt=""
                class="h-5 w-5 rounded-full border border-neutral-800 bg-neutral-800 object-contain"
                loading="lazy"
              />
              <span class="font-medium">{{ tx.institution_name }}</span>
              <span v-if="tx.institution_name && tx.account_name" class="mx-1 text-neutral-500"
                >/</span
              >
              <span>{{ tx.account_name }}</span>
            </td>
            <!-- Amount -->
            <td
              class="px-4 py-2 font-mono text-right text-base font-semibold"
              :class="{
                'text-blue-300': tx.amount > 0,
                'text-red-400': tx.amount < 0,
                'text-neutral-500': tx.amount === 0 || !tx.amount,
              }"
            >
              {{ formatAmount(tx.amount) }}
            </td>
          </tr>
          <tr v-if="transactions.length === 0">
            <td :colspan="5" class="px-4 py-8 text-center text-neutral-500 italic">
              No transactions found.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="flex items-center justify-center gap-4 mt-4" v-if="totalPages > 1">
      <button
        class="btn btn-outline"
        @click="prevPage"
        :disabled="page === 1"
        data-test="prev-page"
      >
        Prev
      </button>
      <span class="text-neutral-400">Page {{ page }} of {{ totalPages }}</span>
      <button
        class="btn btn-outline"
        @click="nextPage"
        :disabled="page >= totalPages"
        data-test="next-page"
      >
        Next
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import Chart from 'chart.js/auto'
import DateRangeSelector from '../DateRangeSelector.vue'
import { fetchTransactions } from '@/api/transactions'
import { formatAmount as formatCurrency } from '@/utils/format'

/**
 * TransactionsTable
 *
 * Displays a paginated table of transactions with date range,
 * account and type filters. Data is fetched from the backend
 * `/transactions` endpoint using the provided filters.
 */
export default {
  name: 'TransactionsTable',
  components: { DateRangeSelector },
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
    const endDate = ref(today.toISOString().slice(0, 10))
    const startDate = ref(
      new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
    )

    const totalPages = computed(() => Math.ceil(total.value / pageSize))

    async function load() {
      const params = {
        page: page.value,
        page_size: pageSize,
        start_date: startDate.value,
        end_date: endDate.value,
      }
      if (accountId.value) params.account_ids = accountId.value
      if (txType.value) params.tx_type = txType.value
      const res = await fetchTransactions(params)
      transactions.value = res.transactions || []
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

    function nextPage() {
      if (page.value < totalPages.value) {
        page.value += 1
        load()
      }
    }
    function prevPage() {
      if (page.value > 1) {
        page.value -= 1
        load()
      }
    }

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
      totalPages,
      formatDate,
      formatAmount,
      formatDescription,
      formatCategory,
      nextPage,
      prevPage,
    }
  },
}
</script>
