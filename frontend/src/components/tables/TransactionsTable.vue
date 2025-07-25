<template>
  <div class="card bg-neutral-950 border border-neutral-800 shadow-xl rounded-2xl p-4 md:p-6">
    <h3 class="font-bold text-xl mb-6 text-left tracking-wide text-blue-300 flex items-center">
      <span class="i-ph:currency-circle-dollar-duotone text-2xl mr-2 text-blue-400"></span>
      Recent Transactions
    </h3>
    <div class="mb-8">
      <canvas ref="transactionsChart" height="110"></canvas>
    </div>
    <div class="overflow-x-auto rounded-xl border border-neutral-800">
      <table class="min-w-full divide-y divide-neutral-800 text-sm">
        <thead class="bg-neutral-900 border-b border-blue-800">
          <tr>
            <th
              class="py-3 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800">
              Date</th>
            <th
              class="py-3 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800">
              Category</th>
            <th
              class="py-3 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800">
              Merchant: Description</th>
            <th
              class="py-3 px-4 text-left font-bold uppercase tracking-wider text-blue-200 border-r border-neutral-800">
              Institution / Account</th>
            <th class="py-3 px-4 text-right font-bold uppercase tracking-wider text-blue-200">Amount</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(tx, i) in sortedTransactions" :key="tx.transaction_id" :class="[
            i % 2 === 0 ? 'bg-neutral-950' : 'bg-neutral-900',
            'hover:bg-blue-950/60 transition-colors duration-100 border-b border-neutral-800'
          ]">
            <!-- Date -->
            <td class="px-4 py-2 font-mono text-xs text-neutral-400">{{ formatDate(tx.date) }}</td>
            <!-- Category -->
            <td class="px-4 py-2 text-center">
              <img v-if="tx.category_icon_url" :src="tx.category_icon_url" alt="category icon"
                class="h-5 w-5 mx-auto" loading="lazy" />
              <span v-else
                class="inline-block rounded-xl border border-blue-800 bg-gradient-to-r from-neutral-900 to-blue-950 px-3 py-1 text-xs font-semibold text-blue-200 tracking-wide shadow-sm">
                {{ formatCategory(tx) }}
              </span>
            </td>
            <!-- Merchant: Description -->
            <td class="px-4 py-2 font-medium text-neutral-100 truncate max-w-xs">
              {{ formatDescription(tx) }}
            </td>
            <!-- Institution: Account with icon -->
            <td class="px-4 py-2 text-xs text-neutral-300 flex items-center gap-2">
              <img v-if="tx.institution_icon_url" :src="tx.institution_icon_url" alt=""
                class="h-5 w-5 rounded-full border border-neutral-800 bg-neutral-800 object-contain" loading="lazy" />
              <span class="font-medium">{{ tx.institution_name }}</span>
              <span v-if="tx.institution_name && tx.account_name" class="mx-1 text-neutral-500">/</span>
              <span>{{ tx.account_name }}</span>
            </td>
            <!-- Amount -->
            <td class="px-4 py-2 font-mono text-right text-base font-semibold" :class="{
              'text-blue-300': tx.amount > 0,
              'text-red-400': tx.amount < 0,
              'text-neutral-500': tx.amount === 0 || !tx.amount
            }">
              {{ formatAmount(tx.amount) }}
            </td>
          </tr>
          <tr v-if="sortedTransactions.length === 0">
            <td :colspan="5" class="px-4 py-8 text-center text-neutral-500 italic">
              No transactions found.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { onMounted, ref, computed } from 'vue'
import Chart from 'chart.js/auto'
import { formatAmount as formatCurrency } from '@/utils/format'

export default {
  name: "TransactionsTable",
  props: {
    transactions: { type: Array, default: () => [] },
    sortKey: String,
    sortOrder: Number,
    search: String
  },
  setup(props) {
    const transactionsChart = ref(null)
    const sortedTransactions = computed(() => [...props.transactions])
    const chartData = computed(() => {
      const map = {}
      props.transactions.forEach(tx => {
        if (!tx.date) return
        const d = new Date(tx.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        map[d] = (map[d] || 0) + Number(tx.amount || 0)
      })
      const keys = Object.keys(map).slice(-7)
      return {
        labels: keys,
        values: keys.map(k => map[k])
      }
    })
    onMounted(() => {
      if (transactionsChart.value) {
        new Chart(transactionsChart.value.getContext('2d'), {
          type: 'line',
          data: {
            labels: chartData.value.labels,
            datasets: [{
              label: 'Daily Net',
              data: chartData.value.values,
              fill: false,
              tension: 0.3,
              borderColor: '#61e8fc',
              backgroundColor: '#61e8fc55',
              pointBorderColor: '#39ff14',
              pointBackgroundColor: '#232e46',
              pointRadius: 5,
              pointHoverRadius: 8,
              borderWidth: 2.5,
            }]
          },
          options: {
            plugins: {
              legend: {
                labels: {
                  color: '#61e8fc',
                  font: { family: 'Fira Mono, monospace', size: 13, weight: 'bold' }
                }
              },
              tooltip: {
                backgroundColor: '#232e46',
                titleColor: '#61e8fc',
                bodyColor: '#e4f5fd',
                borderColor: '#61e8fc',
                borderWidth: 1,
                caretSize: 8,
                displayColors: false
              }
            },
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                grid: { color: 'rgba(97,232,252,0.12)' },
                ticks: { color: '#9bb2cf', font: { family: 'Fira Mono, monospace', size: 12 } }
              },
              y: {
                grid: { color: 'rgba(97,232,252,0.10)' },
                ticks: { color: '#9bb2cf', font: { family: 'Fira Mono, monospace', size: 12 } }
              }
            }
          }
        })
      }
    })
    // Formatting methods
    const formatDate = dateStr => {
      if (!dateStr) return "N/A"
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', {
        year: '2-digit',
        month: 'short',
        day: 'numeric'
      })
    }
    const formatAmount = amount => {
      return formatCurrency(amount)
    }
    const formatAccount = tx => {
      let parts = []
      if (tx.institution_name) parts.push(tx.institution_name)
      if (tx.account_name) parts.push(tx.account_name)
      return parts.length ? parts.join(" ") : "N/A"
    }
    const formatDescription = tx => {
      const merchant = tx.merchant_name ? toTitleCase(tx.merchant_name) : ""
      const desc = tx.description ? literaryFormat(tx.description) : ""
      if (merchant && desc) return `${merchant}: ${desc}`
      if (merchant) return merchant
      if (desc) return desc
      return ""
    }
    const formatCategory = tx => {
      const p = tx.primary_category || ''
      const d = tx.detailed_category || ''
      if (p && d) return `${capitalizeFirst(p)}: ${capitalizeFirst(d)}`
      if (p) return capitalizeFirst(p)
      if (d) return capitalizeFirst(d)
      return "Unknown"
    }
    // Helper functions
    const capitalizeFirst = str => !str ? "" : str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
    const literaryFormat = str => !str ? "" : str.replace(/(^\s*\w|[.!?]\s*\w)/g, s => s.toUpperCase())
    const toTitleCase = str => !str ? "" : str.toLowerCase().replace(/([^\s\/-]+)(?=[\s\/-]?)/g, w => w.charAt(0).toUpperCase() + w.slice(1))
    return {
      transactionsChart,
      sortedTransactions,
      formatDate,
      formatAmount,
      formatAccount,
      formatDescription,
      formatCategory
    }
  }
}
</script>

<style scoped>
.shadow-neon {
  box-shadow: 0 0 8px #39ff14, 0 0 12px #08ffb066;
}
</style>
