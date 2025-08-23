<!--
  AccountSnapshot.vue
  Displays selected accounts with balances and upcoming transactions.
  Clicking an account reveals the last three transactions.
-->
<template>
  <div class="bg-bg-secondary rounded-2xl p-4 shadow-card min-w-[320px] max-w-[480px]">

    <div class="mt-2 space-y-1">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-xs text-gray-400">
            <th class="pb-1">Account</th>
            <th class="pb-1">Balance / <span class="italic text-gray-400">Upcoming</span></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="acc in selectedAccounts" :key="acc.account_id">
            <tr class="border-b border-gray-100 last:border-none cursor-pointer"
              @click="toggleDetails(acc.account_id)" role="button" tabindex="0"
              @keydown.enter="toggleDetails(acc.account_id)" @keydown.space="toggleDetails(acc.account_id)">
              <td class="py-1">
                <span class="block font-semibold text-base truncate max-w-[170px] text-blue-950 dark:text-blue-100"
                  :title="acc.name">{{ acc.name }}</span>
                <span class="block text-xs text-gray-500 font-medium mt-0.5 leading-tight">{{ acc.institution_name
                  }}</span>
              </td>
              <td class="py-1 min-w-[180px] relative group">
                <!-- Balance and Upcoming, same line -->
                <span class="font-mono font-semibold text-base">
                  {{ formatAccounting(acc.balance) }}
                </span>
                <span class="ml-2 font-mono transition-colors duration-150 cursor-pointer faded-upcoming"
                  :class="upcomingClass(netUpcoming(acc))" @mouseenter="hovered = acc.account_id"
                  @mouseleave="hovered = null" @focus="hovered = acc.account_id" @blur="hovered = null" tabindex="0"
                  aria-label="View upcoming transactions">
                  <i class="i-carbon-calendar text-xs mr-1" aria-hidden="true"></i>
                  {{ formatUpcoming(netUpcoming(acc)) }}
                  <!-- Tooltip on hover -->
                  <div v-if="hovered === acc.account_id && upcomingForAccount(acc).length"
                    class="absolute left-1/2 z-10 min-w-[220px] -translate-x-1/2 mt-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-lg rounded-xl p-2 text-xs">
                    <div v-for="(tx, idx) in upcomingForAccount(acc)"
                      :key="tx.id || tx.description + tx.next_due_date + idx"
                      class="flex justify-between gap-2 py-1 border-b border-gray-100 last:border-0">
                      <span>
                        <span class="font-semibold">{{ tx.description }}</span>
                        <span v-if="tx.next_due_date" class="ml-1 text-gray-400">[{{ tx.next_due_date }}]</span>
                      </span>
                      <span class="font-mono" :class="upcomingClass(tx.amount)">
                        {{ formatUpcoming(tx.amount) }}
                      </span>
                    </div>
                  </div>
                </span>
              </td>
            </tr>
            <tr v-if="openAccountId === acc.account_id" class="bg-gray-50 dark:bg-gray-800">
              <td colspan="2" class="py-2">
                <ul>
                  <li v-for="tx in recentTxs[acc.account_id]" :key="tx.id" class="flex justify-between text-xs py-0.5">
                    <span class="text-gray-500">{{ tx.date }}</span>
                    <span class="flex-1 mx-2 truncate">{{ tx.name }}</span>
                    <span class="font-mono">{{ formatAccounting(tx.amount) }}</span>
                  </li>
                  <li v-if="recentTxs[acc.account_id]?.length === 0" class="text-gray-500 text-xs italic py-0.5">
                    No recent transactions
                  </li>
                </ul>
              </td>
            </tr>
          </template>
          <tr v-if="!selectedAccounts.length">
            <td colspan="2" class="text-center text-gray-400 text-sm py-2">No selected accounts.</td>
          </tr>
        </tbody>
        <tfoot>
          <tr class="font-bold border-t border-gray-200 dark:border-gray-800">
            <td class="pt-2">Total</td>
            <td class="pt-2 min-w-[180px] relative">
              <span class="font-mono">
                {{ formatAccounting(totalBalance) }}
              </span>
              <span class="ml-2 font-mono faded-upcoming" :class="upcomingClass(totalUpcoming)">
                <i class="i-carbon-calendar text-xs mr-1" aria-hidden="true"></i>
                {{ formatUpcoming(totalUpcoming) }}
              </span>
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useSnapshotAccounts } from '@/composables/useSnapshotAccounts.js'
import { fetchRecentTransactions } from '@/api/accounts'

const hovered = ref(null)
const { selectedAccounts, reminders } = useSnapshotAccounts()
const openAccountId = ref(null)
const recentTxs = reactive({})

function formatAccounting(val) {
  const num = parseFloat(val || 0)
  const abs = Math.abs(num).toLocaleString('en-US', { style: 'decimal', minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return num < 0 ? `($${abs})` : `$${abs}`
}

function formatUpcoming(val) {
  const num = parseFloat(val || 0)
  const abs = Math.abs(num).toLocaleString('en-US', { style: 'decimal', minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (num === 0) return '$0.00'
  return num > 0 ? `+$${abs}` : `-$${abs}`
}

function upcomingClass(val) {
  const num = parseFloat(val || 0)
  return [
    'ml-2',
    'faded-upcoming',
    num > 0 ? 'text-green-700 dark:text-green-400' : '',
    num < 0 ? 'text-red-400' : '',
    num === 0 ? 'text-gray-400' : '',
  ]
}

const totalBalance = computed(() =>
  selectedAccounts.value.reduce((sum, acc) => sum + parseFloat(acc.balance || 0), 0)
)

const totalUpcoming = computed(() =>
  selectedAccounts.value.reduce((sum, acc) => sum + netUpcoming(acc), 0)
)

function netUpcoming(acc) {
  const list = upcomingForAccount(acc)
  return list.reduce((sum, tx) => sum + (parseFloat(tx.amount) || 0), 0)
}

function upcomingForAccount(acc) {
  const arr =
    Array.isArray(reminders.value)
      ? reminders.value.filter(tx => tx.account_id === acc.account_id)
      : reminders.value[acc.account_id] || []
  return arr
}

/**
 * Toggle recent transaction display for an account.
 * Fetches the last three transactions on first expansion.
 */
function toggleDetails(accountId) {
  openAccountId.value = openAccountId.value === accountId ? null : accountId
  if (openAccountId.value === accountId && !recentTxs[accountId]) {
    fetchRecentTransactions(accountId, 3)
      .then(res => {
        let txs = []
        if (Array.isArray(res?.transactions)) {
          txs = res.transactions
        } else if (Array.isArray(res?.data?.transactions)) {
          txs = res.data.transactions
        } else if (Array.isArray(res?.data)) {
          txs = res.data
        }
        recentTxs[accountId] = txs
      })
      .catch(() => {
        recentTxs[accountId] = []
      })
  }
}
</script>

<style scoped>
.faded-upcoming {
  opacity: 0.65;
  font-style: italic;
}

.faded-upcoming:focus,
.faded-upcoming:hover {
  opacity: 1;
  font-style: normal;
}
</style>
