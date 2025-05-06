<template>
  <div class="p-6 bg-gray-50 min-h-screen space-y-6">
    <h1 class="text-2xl font-bold">Forecast Component Test Harness</h1>

    <button class="border px-2 py-1 rounded bg-white shadow"
      @click="viewType = viewType === 'Month' ? 'Year' : 'Month'">
      Toggle View (Currently: {{ viewType }})
    </button>

    <ForecastLayout :view-type="viewType" :forecast-items="recurringTxs" :account-history="accountHistory"
      :manual-income="manualIncome" :liability-rate="liabilityRate" />

    <div class="overflow-x-auto text-xs font-mono">
      <h2 class="text-lg font-semibold mt-6 mb-2">Engine Output Preview</h2>
      <table class="table-auto border-collapse w-full">
        <thead>
          <tr>
            <th class="px-2">Date</th>
            <th class="px-2">Forecast</th>
            <th class="px-2">Actual</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(label, i) in labels" :key="i">
            <td class="px-2">{{ label }}</td>
            <td class="px-2">{{ forecastLine[i]?.toFixed(2) }}</td>
            <td class="px-2">{{ actualLine[i]?.toFixed(2) ?? '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ForecastLayout from '@/components/forecast/ForecastLayout.vue'
import { useForecastEngine } from '@/composables/useForecastEngine'

// Toggle: Month/Year
const viewType = ref < 'Month' | 'Year' > ('Month')

// Mock Recurring Transactions
const recurringTxs = [
  { amount: 1500, frequency: 'monthly', next_due_date: '2025-05-01' },
  { amount: -400, frequency: 'weekly', next_due_date: '2025-05-03' }
]

// Historical Account Balances
const accountHistory = [
  { date: '2025-05-01', balance: 2500 },
  { date: '2025-05-02', balance: 2550 },
  { date: '2025-05-03', balance: 2600 }
]

// Manual controls
const manualIncome = 0
const liabilityRate = 0

// Engine output
const { labels, forecastLine, actualLine } = useForecastEngine(
  viewType,
  recurringTxs,
  accountHistory,
  manualIncome,
  liabilityRate
)
</script>

<style scoped>
/* Matches dashboard vibe */
</style>
