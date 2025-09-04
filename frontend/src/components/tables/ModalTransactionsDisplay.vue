<template>
  <div
    class="overflow-x-auto rounded-xl shadow bg-[var(--color-bg-secondary)] text-[var(--color-text-light)] px-4 py-4 border border-[var(--color-accent-cyan)]/30"
  >
    <!-- Title Date Above Table -->
    <div v-if="titleDate" class="mb-2 ml-2 text-base font-medium">
      {{ titleDate }}
    </div>
    <table class="min-w-full text-sm rounded-lg overflow-hidden">
      <thead>
        <tr class="bg-[var(--color-bg-dark)] text-[var(--color-text-light)]">
          <th class="pl-8 pr-6 py-4 font-semibold text-left">Account</th>
          <th class="px-6 py-4 font-semibold text-left">Merchant</th>
          <th class="px-6 py-4 text-right font-semibold">Amount</th>
          <th v-if="showDateColumn" class="px-6 py-4 text-right font-semibold">Date</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="tx in transactions"
          :key="tx.transaction_id"
          :class="[
            'group transition-colors border-b border-[var(--divider)] bg-[var(--surface)] hover:bg-[var(--hover-bg)] cursor-pointer',
          ]"
          @click="$emit('row-click', tx)"
        >
          <!-- Account column with accent bar and institution badge -->
          <td class="pl-8 pr-2 py-4 relative min-w-[140px]">
            <div
              :class="[
                'absolute left-0 top-5 bottom-3 w-0.5 rounded-full opacity-90',
                tx.amount > 0 ? 'bg-[var(--color-accent-green)]' : 'bg-[var(--color-accent-red)]',
              ]"
            ></div>
            <div class="pl-4 flex items-center gap-2">
              <img
                v-if="tx.institution_icon_url"
                :src="tx.institution_icon_url"
                alt="Institution logo"
                class="h-6 w-6 rounded-full object-contain"
              />
              <span
                v-else
                class="h-6 w-6 rounded-full bg-[var(--color-accent-purple)] flex items-center justify-center text-xs font-semibold text-[var(--color-text-dark)]"
              >
                {{ initials(tx.institution_name) }}
              </span>
              <div class="flex flex-col">
                <div class="font-bold text-base">{{ tx.account_name }}</div>
                <div class="text-xs text-[var(--color-text-muted)]">{{ tx.institution_name }}</div>
              </div>
            </div>
          </td>
          <td class="px-6 py-4">
            <div class="flex items-start gap-2">
              <img
                v-if="showCategoryVisuals && tx.category_icon_url"
                :src="tx.category_icon_url"
                alt="Category icon"
                class="h-6 w-6 object-contain filter drop-shadow-sm flex-shrink-0"
              />
              <div class="flex flex-col flex-1">
                <div class="font-semibold truncate">{{ tx.merchant_name }}</div>
                <div class="text-xs text-[var(--color-text-muted)] truncate">
                  {{ tx.description }}
                </div>
                <div
                  v-if="showCategoryVisuals && tx.category && tx.category.length"
                  class="text-xs text-[var(--color-accent-purple)] italic mt-1"
                >
                  {{ tx.category[0]
                  }}<span v-if="tx.category.length > 1">: {{ tx.category[1] }}</span>
                </div>
              </div>
            </div>
          </td>
          <td class="px-6 py-4 text-right">
            <span
              :class="[
                'font-bold tracking-tight group-hover:opacity-80',
                tx.amount > 0
                  ? 'text-[var(--color-accent-green)]'
                  : tx.amount < 0
                    ? 'text-[var(--color-accent-red)]'
                    : 'text-[var(--color-text-light)]',
              ]"
            >
              {{ formatAmount(tx.amount) }}
            </span>
          </td>
          <td v-if="showDateColumn" class="px-6 py-4 text-right text-[var(--color-text-muted)]">
            {{ formatDate(tx.date || tx.transaction_date) }}
          </td>
        </tr>
        <tr v-if="!transactions.length">
          <td
            :colspan="showDateColumn ? 4 : 3"
            class="px-6 py-8 italic text-center text-[var(--color-text-muted)] bg-[var(--color-bg-secondary)] rounded-b-xl"
          >
            No transactions found.
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { formatAmount as utilFormatAmount } from '../../utils/format'

defineProps({
  transactions: { type: Array, default: () => [] },
  titleDate: { type: String, default: '' },
  showDateColumn: { type: Boolean, default: false },
  showCategoryVisuals: { type: Boolean, default: true },
})

/**
 * Format a numeric amount using shared currency helpers.
 */
function formatAmount(amount) {
  if (amount == null) return '-'
  return utilFormatAmount(amount)
}
/**
 * Generate initials from a name string (up to 2 chars).
 */
function initials(name) {
  if (!name) return '??'
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

/**
 * Normalize date display to YYYY-MM-DD.
 */
function formatDate(value) {
  if (!value) return ''
  if (typeof value === 'string') {
    // If already ISO-like, take first 10 chars
    if (value.length >= 10 && /\d{4}-\d{2}-\d{2}/.test(value)) return value.slice(0, 10)
    // Try to parse and reformat
    const d = new Date(value)
    if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10)
    return value
  }
  if (value instanceof Date && !isNaN(value.getTime())) {
    return value.toISOString().slice(0, 10)
  }
  return String(value)
}
</script>
