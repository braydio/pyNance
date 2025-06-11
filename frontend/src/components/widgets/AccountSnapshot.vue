<template>
  <div class="card space-y-4">
    <div class="flex-between">
      <h2 class="text-xl font-semibold">Account Snapshot</h2>
      <button class="btn btn-sm btn-outline" @click="showConfig = !showConfig">
        {{ showConfig ? 'Done' : 'Configure' }}
      </button>
    </div>

    <div v-if="showConfig" class="space-y-2">
      <p class="text-sm text-gray-400">Select up to 5 accounts</p>
      <div v-for="acc in accounts" :key="acc.account_id" class="flex items-center gap-2">
        <input
          type="checkbox"
          :id="acc.account_id"
          v-model="selectedIds"
          :value="acc.account_id"
          :disabled="!selectedIds.includes(acc.account_id) && selectedIds.length >= 5"
        />
        <label :for="acc.account_id">{{ acc.institution_name || acc.name }}</label>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="acc in selectedAccounts"
        :key="acc.account_id"
        class="p-4 bg-[var(--color-bg-dark)] rounded-lg shadow space-y-1"
      >
        <div class="font-semibold">{{ acc.name }}</div>
        <div class="text-sm text-gray-400">{{ acc.institution_name }}</div>
        <div class="text-right font-mono text-green-400">
          {{ formatCurrency(acc.balance) }}
        </div>
        <ul v-if="reminders[acc.account_id]?.length" class="mt-2 text-sm space-y-1">
          <li
            v-for="rem in reminders[acc.account_id]"
            :key="rem.description + rem.next_due_date"
            class="flex justify-between gap-2"
          >
            <span class="flex-1">{{ rem.description }}</span>
            <span class="font-mono">{{ formatCurrency(rem.amount) }}</span>
            <span class="text-xs text-gray-500">{{ rem.next_due_date }}</span>
          </li>
        </ul>
        <p v-else class="text-sm text-gray-500 mt-2 italic">No upcoming bills</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useSnapshotAccounts } from '@/composables/useSnapshotAccounts.js'

const showConfig = ref(false)
const { accounts, selectedAccounts, selectedIds, reminders } = useSnapshotAccounts()

function formatCurrency(val) {
  const num = parseFloat(val || 0)
  return num.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  })
}
</script>

<style scoped>
</style>
