<!--
  RecentTransactions.vue
  Displays the most recent transactions across all accounts.
-->
<template>
  <div class="flex-1 min-w-[340px] max-w-[400px] bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-red)] p-6 flex flex-col">
    <h2 class="text-2xl font-bold mb-4 text-[var(--color-accent-red)] text-center">Recent Transactions</h2>
    <ul class="space-y-1">
      <li v-for="tx in transactions" :key="tx.id" class="flex justify-between text-sm">
        <span class="text-gray-500">{{ tx.date }}</span>
        <span class="flex-1 mx-2 truncate">{{ tx.name }}</span>
        <span class="font-mono">{{ formatAmount(tx.amount) }}</span>
      </li>
      <li v-if="!transactions.length" class="text-gray-500 italic text-sm text-center">
        No recent transactions
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchTransactions } from '@/api/transactions'

const transactions = ref([])

function formatAmount(val) {
  const num = parseFloat(val || 0)
  const abs = Math.abs(num).toLocaleString('en-US', { style: 'decimal', minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return num < 0 ? `($${abs})` : `$${abs}`
}

onMounted(async () => {
  try {
    const res = await fetchTransactions({ limit: 3, recent: true })
    let txs = []
    if (Array.isArray(res?.transactions)) {
      txs = res.transactions
    } else if (Array.isArray(res?.data?.transactions)) {
      txs = res.data.transactions
    } else if (Array.isArray(res?.data)) {
      txs = res.data
    }
    transactions.value = txs
  } catch {
    transactions.value = []
  }
})
</script>
