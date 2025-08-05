<template>
  <div class="overflow-x-auto rounded-xl shadow bg-transparent px-2 py-2">
    <!-- Title Date Above Table -->
    <div v-if="titleDate" class="mb-2 ml-2 text-violet-200 text-base font-medium">
      {{ titleDate }}
    </div>
    <table class="min-w-full text-sm rounded-lg overflow-hidden bg-transparent">
      <thead>
        <tr class="bg-gradient-to-r from-violet-900/90 via-blue-900/80 to-slate-800/80 text-violet-100">
          <th class="pl-8 pr-6 py-4 font-semibold text-left">Account</th>
          <th class="px-6 py-4 font-semibold text-left">Merchant</th>
          <th class="px-6 py-4 text-right font-semibold">Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="tx in transactions" :key="tx.transaction_id" :class="[
          'group transition-all border-b border-violet-800/30',
          'hover:scale-[1.015] hover:shadow-lg hover:z-10'
        ]" style="background: linear-gradient(90deg, rgba(58,0,120,0.09) 0%, rgba(40,30,80,0.12) 100%);">
          <!-- Account column with accent bar -->
          <td class="pl-8 pr-2 py-4 relative min-w-[120px]">
            <div :class="[
              'absolute left-0 top-5 bottom-3 w-0.5 rounded-full',
              tx.amount > 0 ? 'bg-emerald-300/90' : 'bg-rose-400/90'
            ]"></div>
            <div class="pl-4 text-violet-100">
              <div class="font-bold text-base">{{ tx.account_name }}</div>
              <div class="text-xs text-violet-300">{{ tx.institution_name }}</div>
            </div>
          </td>
          <td class="px-6 py-4 text-violet-100">
            <div class="flex items-center">
              <img v-if="tx.category_icon_url" :src="tx.category_icon_url" alt="Category Icon"
                class="h-7 w-7 mr-2 object-contain filter drop-shadow" />
              <div class="flex flex-col">
                <div class="font-semibold">{{ tx.merchant_name }}</div>
                <div class="text-xs text-violet-300">{{ tx.description }}</div>
              </div>
            </div>
          </td>
          <td class="px-6 py-4 text-right">
            <span :class="[
              'font-bold tracking-tight',
              tx.amount > 0
                ? 'text-emerald-300 group-hover:text-emerald-200'
                : tx.amount < 0
                  ? 'text-rose-300 group-hover:text-rose-200'
                  : 'text-violet-100'
            ]">
              {{ formatAmount(tx.amount) }}
            </span>
          </td>
        </tr>
        <tr v-if="!transactions.length">
          <td colspan="3" class="px-6 py-8 italic text-center text-violet-300 bg-violet-900/60 rounded-b-xl">
            No transactions found.
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'
import { formatAmount as utilFormatAmount } from '../../utils/format'

defineProps({
  transactions: { type: Array, default: () => [] },
  titleDate: { type: String, default: '' }
})

function formatAmount(amount) {
  if (amount == null) return '-'
  return utilFormatAmount(amount)
}
</script>
