<template>
  <div class="card space-y-4">
    <div class="flex-between">
      <h2 class="text-xl font-semibold">Account Snapshot</h2>
      <button class="btn btn-sm btn-outline" @click="toggleConfig">
        {{ showConfig ? 'Done' : 'Configure' }}
      </button>
    </div>

    <div v-if="showConfig" class="relative">
      <FuzzyDropdown
        :options="accounts"
        v-model="selectedIds"
        :max="5"
        class="w-64"
      />
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
    <div class="text-right font-semibold pt-2">
      Total Balance: {{ formatCurrency(totalBalance) }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import FuzzyDropdown from '@/components/ui/FuzzyDropdown.vue'
import { useSnapshotAccounts } from '@/composables/useSnapshotAccounts.js'

const showConfig = ref(false)
const { accounts, selectedAccounts, selectedIds, reminders } = useSnapshotAccounts()

function toggleConfig() {
  showConfig.value = !showConfig.value
}

const totalBalance = computed(() =>
  selectedAccounts.value.reduce((sum, acc) => sum + parseFloat(acc.balance || 0), 0)
)

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
.card {
  @apply bg-[var(--color-bg-secondary)] border border-[var(--divider)] p-4 rounded-lg shadow;
}
</style>
