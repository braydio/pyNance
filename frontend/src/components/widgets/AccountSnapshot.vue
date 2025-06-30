<template>
  <div class="bg-bg-secondary rounded-2xl p-4 shadow-card min-w-[280px] max-w-[420px]">
    <!-- Header Row -->
    <div class="flex items-center justify-between mb-1">
      <span class="text-lg font-bold tracking-tight">Accounts</span>
      <div class="flex items-center gap-2">
        <button class="text-xs px-2 py-1 rounded border hover:bg-bg-dark transition"
          :class="showUpcoming ? 'border-accent-mint text-accent-mint' : 'border-gray-300 text-gray-500'"
          @click="toggleUpcoming">{{ showUpcoming ? 'Hide Upcoming' : 'Show Upcoming' }}</button>
        <button class="text-gray-400 hover:text-accent-mint p-1" @click="toggleConfig"
          :title="showConfig ? 'Done' : 'Configure'">
          <span v-if="showConfig">✓</span>
          <i v-else class="i-carbon-settings"></i>
        </button>
      </div>
    </div>

    <!-- Config Mode (account picker) -->
    <div v-if="showConfig" class="my-2">
      <FuzzyDropdown :options="accounts" v-model="selectedIds" :max="5" class="w-full" />
    </div>

    <!-- Account List -->
    <div class="mt-2 space-y-1">
      <div v-for="acc in selectedAccounts" :key="acc.account_id"
        class="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 last:border-none py-2 gap-2">
        <div class="min-w-0 flex-1">
          <span class="block font-semibold text-base truncate max-w-[170px] text-blue-950 dark:text-blue-100"
            :title="acc.name">{{ acc.name }}</span>
          <span class="block text-xs text-gray-500 font-medium mt-0.5 leading-tight">{{ acc.institution_name }}</span>
        </div>
        <div class="text-right min-w-[120px] font-mono font-semibold text-base flex flex-col items-end gap-0.5">
          <span :class="['account-balance', 'text-blue-700', 'dark:text-blue-300']">{{ formatAccounting(acc.balance)
            }}</span>
        </div>
      </div>
      <div v-if="selectedAccounts.length === 0" class="text-center text-gray-400 text-sm py-2">No selected accounts.
      </div>
    </div>

    <!-- Total -->
    <div
      class="flex justify-between items-center mt-4 font-semibold text-lg border-t pt-2 border-gray-200 dark:border-gray-800">
      <span>Total</span>
      <span class="font-mono" :class="totalBalance >= 0 ? 'text-[#38ffd4]' : 'text-red-400'">{{
        formatAccounting(totalBalance) }}</span>
    </div>

    <!-- Upcoming Transactions Toggle Drawer -->
    <div v-if="showUpcoming" class="mt-4 rounded-xl bg-[#e0fcfa] dark:bg-[#102726] px-3 py-2 border border-accent-mint">
      <div class="text-sm font-bold text-accent-mint mb-1 flex items-center gap-2">
        <i class="i-carbon-calendar"></i>
        Upcoming Transactions
      </div>
      <ul class="divide-y divide-accent-mint/20 text-sm">
        <li v-for="(rem, idx) in allUpcomingReminders" :key="rem.description + rem.next_due_date + rem.account_id + idx"
          class="flex justify-between items-center py-1">
          <span class="truncate max-w-[180px]" :title="rem.description">
            {{ rem.description }}
            <span class="ml-1 text-xs text-gray-400 font-normal">({{ rem.accountName }})</span>
            <span class="ml-1 text-xs text-gray-400" v-if="rem.next_due_date">[{{ rem.next_due_date }}]</span>
          </span>
          <span class="font-mono"
            :class="rem.amount < 0 ? 'text-red-400' : rem.amount > 0 ? 'text-green-700' : 'text-gray-500'"
            v-if="rem.amount !== undefined">{{ formatAccounting(rem.amount) }}</span>
        </li>
        <li v-if="!allUpcomingReminders.length" class="text-gray-400 text-xs py-2 text-center">No upcoming transactions
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import FuzzyDropdown from '@/components/ui/FuzzyDropdown.vue'
import { useSnapshotAccounts } from '@/composables/useSnapshotAccounts.js'

const showConfig = ref(false)
const showUpcoming = ref(false)
const { accounts, selectedAccounts, selectedIds, reminders } = useSnapshotAccounts()

const toggleConfig = () => { showConfig.value = !showConfig.value }
const toggleUpcoming = () => { showUpcoming.value = !showUpcoming.value }

const totalBalance = computed(() =>
  selectedAccounts.value.reduce((sum, acc) => sum + parseFloat(acc.balance || 0), 0)
)

// Accounting format: "$ 1,234.56" for positive, "($ 1,234.56)" for negative
function formatAccounting(val) {
  const num = parseFloat(val || 0)
  const abs = Math.abs(num).toLocaleString('en-US', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
  if (num < 0) {
    return `($ ${abs})`
  }
  return `$ ${abs}`
}

// Get all reminders (aka "upcoming transactions") for selected accounts as a single array
const allUpcomingReminders = computed(() => {
  // reminders: { [account_id]: [ { description, amount?, next_due_date? } ] }
  // Attach accountName for display
  return selectedAccounts.value.flatMap(acc =>
    (reminders[acc.account_id] || []).map(rem => ({
      ...rem,
      account_id: acc.account_id,
      accountName: acc.name
    }))
  )
})
</script>
